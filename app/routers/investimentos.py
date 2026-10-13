from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.deps import Sessao, UsuarioAtual
from app.domain.rentabilidade import Premissas, projetar
from app.models import Investimento
from app.routers.premissas import PremissasDep
from app.schemas import (
    InvestimentoCriar,
    InvestimentoSaida,
    PremissasSaida,
    ProjecaoInvestimento,
    ProjecaoSaida,
)

router = APIRouter(prefix="/investimentos", tags=["investimentos"])


async def _buscar(sessao: Sessao, usuario_id: int, investimento_id: int) -> Investimento:
    investimento = await sessao.get(Investimento, investimento_id)
    # Investimento de outro usuário responde 404 para não revelar que existe.
    if investimento is None or investimento.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Investimento não encontrado")
    return investimento


def premissas_saida(p: Premissas) -> PremissasSaida:
    def pct(v: Decimal) -> Decimal:
        return (v * 100).quantize(Decimal("0.01"))

    return PremissasSaida(cdi=pct(p.cdi), selic=pct(p.selic), ipca=pct(p.ipca))


@router.post("", response_model=InvestimentoSaida, status_code=status.HTTP_201_CREATED)
async def criar(dados: InvestimentoCriar, usuario: UsuarioAtual, sessao: Sessao) -> Investimento:
    investimento = Investimento(**dados.model_dump(), usuario_id=usuario.id)
    sessao.add(investimento)
    await sessao.commit()
    return investimento


@router.get("", response_model=list[InvestimentoSaida])
async def listar(usuario: UsuarioAtual, sessao: Sessao) -> Sequence[Investimento]:
    consulta = (
        select(Investimento)
        .where(Investimento.usuario_id == usuario.id)
        .order_by(Investimento.data_vencimento)
    )
    return (await sessao.scalars(consulta)).all()


@router.get("/{investimento_id}", response_model=InvestimentoSaida)
async def detalhar(investimento_id: int, usuario: UsuarioAtual, sessao: Sessao) -> Investimento:
    return await _buscar(sessao, usuario.id, investimento_id)


@router.put("/{investimento_id}", response_model=InvestimentoSaida)
async def atualizar(
    investimento_id: int, dados: InvestimentoCriar, usuario: UsuarioAtual, sessao: Sessao
) -> Investimento:
    investimento = await _buscar(sessao, usuario.id, investimento_id)
    for campo, valor in dados.model_dump().items():
        setattr(investimento, campo, valor)
    await sessao.commit()
    return investimento


@router.delete("/{investimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover(investimento_id: int, usuario: UsuarioAtual, sessao: Sessao) -> Response:
    investimento = await _buscar(sessao, usuario.id, investimento_id)
    await sessao.delete(investimento)
    await sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{investimento_id}/projecao", response_model=ProjecaoInvestimento)
async def projecao(
    investimento_id: int,
    usuario: UsuarioAtual,
    sessao: Sessao,
    premissas: PremissasDep,
    data_resgate: Annotated[date | None, Query(description="Padrão: data de vencimento")] = None,
) -> ProjecaoInvestimento:
    inv = await _buscar(sessao, usuario.id, investimento_id)
    try:
        resultado = projetar(
            tipo=inv.tipo,
            indexador=inv.indexador,
            taxa=inv.taxa,
            valor_aplicado=inv.valor_aplicado,
            data_aplicacao=inv.data_aplicacao,
            data_vencimento=inv.data_vencimento,
            data_resgate=data_resgate or inv.data_vencimento,
            premissas=premissas,
        )
    except ValueError as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erro)) from erro
    return ProjecaoInvestimento(
        investimento=InvestimentoSaida.model_validate(inv),
        premissas=premissas_saida(premissas),
        projecao=ProjecaoSaida(**asdict(resultado)),
    )
