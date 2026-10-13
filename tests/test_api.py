from decimal import Decimal

from httpx import AsyncClient

from tests.conftest import autenticar

CDB = {
    "nome": "CDB Banco X 110% CDI",
    "emissor": "Banco X",
    "tipo": "CDB",
    "indexador": "CDI",
    "taxa": "110",
    "valor_aplicado": "10000.00",
    "data_aplicacao": "2025-01-02",
    "data_vencimento": "2027-01-04",
}
TESOURO_IPCA = {
    "nome": "Tesouro IPCA+ 2029",
    "emissor": "Tesouro Nacional",
    "tipo": "TESOURO_IPCA",
    "indexador": "IPCA",
    "taxa": "7.5",
    "valor_aplicado": "5000.00",
    "data_aplicacao": "2025-03-10",
    "data_vencimento": "2029-05-15",
}


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.json() == {"status": "ok"}


async def test_registro_login_e_me(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get("/auth/me", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["email"] == "ana@exemplo.com"
    assert "senha_hash" not in resp.json()


async def test_email_duplicado(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.post(
        "/auth/registro",
        json={"nome": "Ana", "email": "ana@exemplo.com", "senha": "outra-senha-123"},
    )
    assert resp.status_code == 409


async def test_senha_errada(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.post("/auth/token", data={"username": "ana@exemplo.com", "password": "x"})
    assert resp.status_code == 401


async def test_rotas_exigem_token(client: AsyncClient) -> None:
    assert (await client.get("/investimentos")).status_code == 401
    resp = await client.get("/investimentos", headers={"Authorization": "Bearer invalido"})
    assert resp.status_code == 401


async def test_crud_investimento(client: AsyncClient, auth: dict[str, str]) -> None:
    criado = await client.post("/investimentos", json=CDB, headers=auth)
    assert criado.status_code == 201
    inv_id = criado.json()["id"]

    lista = await client.get("/investimentos", headers=auth)
    assert [i["id"] for i in lista.json()] == [inv_id]

    alterado = await client.put(
        f"/investimentos/{inv_id}", json={**CDB, "taxa": "115"}, headers=auth
    )
    assert Decimal(alterado.json()["taxa"]) == 115

    assert (await client.delete(f"/investimentos/{inv_id}", headers=auth)).status_code == 204
    assert (await client.get(f"/investimentos/{inv_id}", headers=auth)).status_code == 404


async def test_validacoes_de_negocio(client: AsyncClient, auth: dict[str, str]) -> None:
    datas_invertidas = {**CDB, "data_vencimento": "2024-01-01"}
    tesouro_errado = {**TESOURO_IPCA, "indexador": "CDI"}
    cdb_selic = {**CDB, "indexador": "SELIC"}
    for corpo in (datas_invertidas, tesouro_errado, cdb_selic):
        resp = await client.post("/investimentos", json=corpo, headers=auth)
        assert resp.status_code == 422, corpo


async def test_usuario_nao_ve_investimento_de_outro(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    inv_id = (await client.post("/investimentos", json=CDB, headers=auth)).json()["id"]
    outro = await autenticar(client, "bruno@exemplo.com")
    assert (await client.get("/investimentos", headers=outro)).json() == []
    assert (await client.get(f"/investimentos/{inv_id}", headers=outro)).status_code == 404
    assert (await client.delete(f"/investimentos/{inv_id}", headers=outro)).status_code == 404


async def test_projecao_ate_o_vencimento(client: AsyncClient, auth: dict[str, str]) -> None:
    inv_id = (await client.post("/investimentos", json=CDB, headers=auth)).json()["id"]
    resp = await client.get(f"/investimentos/{inv_id}/projecao?cdi=14.9", headers=auth)
    assert resp.status_code == 200
    corpo = resp.json()
    proj = corpo["projecao"]
    assert proj["data_resgate"] == "2027-01-04"
    assert Decimal(proj["aliquota_ir"]) == Decimal("0.15")
    assert Decimal(proj["valor_liquido"]) < Decimal(proj["valor_bruto"])
    assert Decimal(proj["valor_liquido"]) > 10000
    assert corpo["premissas"]["cdi"] == "14.90"


async def test_projecao_com_data_invalida(client: AsyncClient, auth: dict[str, str]) -> None:
    inv_id = (await client.post("/investimentos", json=CDB, headers=auth)).json()["id"]
    resp = await client.get(
        f"/investimentos/{inv_id}/projecao?data_resgate=2030-01-01", headers=auth
    )
    assert resp.status_code == 422


async def test_resumo_da_carteira(client: AsyncClient, auth: dict[str, str]) -> None:
    await client.post("/investimentos", json=CDB, headers=auth)
    await client.post("/investimentos", json=TESOURO_IPCA, headers=auth)
    resp = await client.get("/carteira/resumo?data_referencia=2026-01-02", headers=auth)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["quantidade"] == 2
    assert Decimal(corpo["valor_aplicado"]) == Decimal("15000.00")
    assert Decimal(corpo["valor_liquido"]) > Decimal("15000")
    assert Decimal(corpo["impostos"]) > 0
    assert sum(Decimal(t["participacao"]) for t in corpo["por_tipo"]) == Decimal("1")


async def test_resumo_de_carteira_vazia(client: AsyncClient, auth: dict[str, str]) -> None:
    corpo = (await client.get("/carteira/resumo", headers=auth)).json()
    assert corpo["quantidade"] == 0
    assert Decimal(corpo["valor_liquido"]) == 0
