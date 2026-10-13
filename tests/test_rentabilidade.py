from datetime import date
from decimal import Decimal

import pytest

from app.domain.rentabilidade import Premissas, fator_correcao, projetar
from app.domain.tipos import Indexador, TipoTitulo

PREMISSAS = Premissas(cdi=Decimal("0.149"), selic=Decimal("0.15"), ipca=Decimal("0.048"))


def test_prefixado_252_dias_uteis_rende_a_taxa_anual() -> None:
    fator = fator_correcao(Indexador.PREFIXADO, Decimal("12"), 252, PREMISSAS)
    assert fator == pytest.approx(Decimal("1.12"))


def test_cdi_100_por_cento_aproxima_o_cdi_anual() -> None:
    fator = fator_correcao(Indexador.CDI, Decimal("100"), 252, PREMISSAS)
    # O arredondamento do CDI diário em 8 casas gera diferença na 6ª casa.
    assert abs(fator - Decimal("1.149")) < Decimal("0.00001")


def test_cdi_110_rende_mais_que_cdi_100() -> None:
    f100 = fator_correcao(Indexador.CDI, Decimal("100"), 252, PREMISSAS)
    f110 = fator_correcao(Indexador.CDI, Decimal("110"), 252, PREMISSAS)
    assert (f110 - 1) / (f100 - 1) == pytest.approx(Decimal("1.1"), rel=Decimal("0.01"))


def test_ipca_mais_spread_compoe_as_taxas() -> None:
    fator = fator_correcao(Indexador.IPCA, Decimal("7"), 252, PREMISSAS)
    assert fator == pytest.approx(Decimal("1.048") * Decimal("1.07"))


def test_selic_mais_spread_compoe_as_taxas() -> None:
    fator = fator_correcao(Indexador.SELIC, Decimal("0.1"), 252, PREMISSAS)
    assert fator == pytest.approx(Decimal("1.15") * Decimal("1.001"))


def _cdb(**kwargs: object) -> dict[str, object]:
    base: dict[str, object] = {
        "tipo": TipoTitulo.CDB,
        "indexador": Indexador.PREFIXADO,
        "taxa": Decimal("12"),
        "valor_aplicado": Decimal("10000"),
        "data_aplicacao": date(2024, 12, 31),
        "data_vencimento": date(2027, 12, 31),
        "premissas": PREMISSAS,
    }
    base.update(kwargs)
    return base


def test_cdb_prefixado_um_ano() -> None:
    # 2025 tem 252 dias úteis e 365 dias corridos: IR de 17,5%.
    p = projetar(**_cdb(data_resgate=date(2025, 12, 31)))  # type: ignore[arg-type]
    bruto = Decimal("10000") * Decimal("1.12") ** (Decimal(252) / 252)
    assert p.dias_uteis == 252
    assert p.dias_corridos == 365
    assert p.valor_bruto == bruto.quantize(Decimal("0.01"))
    assert p.iof == 0
    assert p.aliquota_ir == Decimal("0.175")
    assert p.ir == ((bruto - 10000) * Decimal("0.175")).quantize(Decimal("0.01"))
    assert p.valor_liquido == p.valor_bruto - p.ir


def test_resgate_em_menos_de_30_dias_cobra_iof_antes_do_ir() -> None:
    p = projetar(**_cdb(data_resgate=date(2025, 1, 15)))  # type: ignore[arg-type]
    assert p.dias_corridos == 15
    assert p.iof == (p.rendimento_bruto * Decimal("0.50")).quantize(Decimal("0.01"))
    esperado_ir = (p.rendimento_bruto - p.iof) * Decimal("0.225")
    assert abs(p.ir - esperado_ir) <= Decimal("0.01")


def test_lci_e_isenta() -> None:
    p = projetar(**_cdb(tipo=TipoTitulo.LCI, data_resgate=date(2025, 12, 31)))  # type: ignore[arg-type]
    assert p.ir == 0
    assert p.iof == 0
    assert p.valor_liquido == p.valor_bruto
    assert p.rentabilidade_liquida == p.rentabilidade_bruta


def test_resgate_no_dia_da_aplicacao_nao_rende() -> None:
    p = projetar(**_cdb(data_resgate=date(2024, 12, 31)))  # type: ignore[arg-type]
    assert p.valor_bruto == Decimal("10000.00")
    assert p.valor_liquido == Decimal("10000.00")


@pytest.mark.parametrize("resgate", [date(2024, 12, 30), date(2028, 1, 1)])
def test_resgate_fora_do_prazo_e_invalido(resgate: date) -> None:
    with pytest.raises(ValueError):
        projetar(**_cdb(data_resgate=resgate))  # type: ignore[arg-type]
