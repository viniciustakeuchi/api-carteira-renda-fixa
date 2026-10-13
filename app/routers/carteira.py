from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.deps import Sessao, UsuarioAtual
from app.domain.rentabilidade import projetar
from app.domain.tipos import TipoTitulo
from app.models import Investimento
from app.routers.investimentos import premissas_saida
from app.routers.premissas import PremissasDep
from app.schemas import ResumoCarteira, TotalPorTipo

router = APIRouter(prefix="/carteira", tags=["carteira"])


@router.get("/resumo", response_model=ResumoCarteira)
async def resumo(
    usuario: UsuarioAtual,
    sessao: Sessao,
    premissas: PremissasDep,
    data_referencia: Annotated[date | None, Query(description="Padrão: hoje")] = None,
) -> ResumoCarteira:
    """Posição da carteira na data: cada título é marcado até a data ou até o seu vencimento."""
    referencia = data_referencia or date.today()
    investimentos = (
        await sessao.scalars(select(Investimento).where(Investimento.usuario_id == usuario.id))
    ).all()

    aplicado: dict[TipoTitulo, Decimal] = defaultdict(Decimal)
    liquido: dict[TipoTitulo, Decimal] = defaultdict(Decimal)
    total_bruto = Decimal(0)
    for inv in investimentos:
        data = min(max(referencia, inv.data_aplicacao), inv.data_vencimento)
        p = projetar(
            tipo=inv.tipo,
            indexador=inv.indexador,
            taxa=inv.taxa,
            valor_aplicado=inv.valor_aplicado,
            data_aplicacao=inv.data_aplicacao,
            data_vencimento=inv.data_vencimento,
            data_resgate=data,
            premissas=premissas,
        )
        aplicado[inv.tipo] += inv.valor_aplicado
        liquido[inv.tipo] += p.valor_liquido
        total_bruto += p.valor_bruto

    total_liquido = sum(liquido.values(), Decimal(0))
    por_tipo = [
        TotalPorTipo(
            tipo=tipo,
            valor_aplicado=aplicado[tipo],
            valor_liquido=liquido[tipo],
            participacao=(liquido[tipo] / total_liquido).quantize(Decimal("0.0001")),
        )
        for tipo in sorted(liquido, key=lambda t: liquido[t], reverse=True)
    ]
    return ResumoCarteira(
        data_referencia=referencia,
        premissas=premissas_saida(premissas),
        quantidade=len(investimentos),
        valor_aplicado=sum(aplicado.values(), Decimal(0)),
        valor_bruto=total_bruto,
        valor_liquido=total_liquido,
        impostos=total_bruto - total_liquido,
        por_tipo=por_tipo,
    )
