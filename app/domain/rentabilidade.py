"""Projeção de rentabilidade de títulos de renda fixa.

Convenções do mercado brasileiro:
- Taxas anuais em base 252 dias úteis: fator = (1 + taxa) ** (du / 252).
- CDI diário arredondado em 8 casas, como divulgado pela B3, e aplicado
  ao percentual contratado: fator_dia = 1 + cdi_dia * percentual.
- IR e IOF contam dias corridos; a rentabilidade conta dias úteis.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.domain.calendario import dias_uteis_entre
from app.domain.tipos import Indexador, TipoTitulo
from app.domain.tributacao import aliquota_iof, aliquota_ir

CENTAVO = Decimal("0.01")
BASE_ANUAL = Decimal(252)


@dataclass(frozen=True)
class Premissas:
    """Taxas anuais projetadas, em fração (0.1490 = 14,90% a.a.)."""

    cdi: Decimal
    selic: Decimal
    ipca: Decimal


@dataclass(frozen=True)
class Projecao:
    data_resgate: date
    dias_corridos: int
    dias_uteis: int
    valor_bruto: Decimal
    rendimento_bruto: Decimal
    iof: Decimal
    ir: Decimal
    aliquota_ir: Decimal
    valor_liquido: Decimal
    rentabilidade_bruta: Decimal
    rentabilidade_liquida: Decimal


def _fator_anual(taxa: Decimal, du: int) -> Decimal:
    return (1 + taxa) ** (Decimal(du) / BASE_ANUAL)


def fator_correcao(indexador: Indexador, taxa: Decimal, du: int, premissas: Premissas) -> Decimal:
    """Fator acumulado do título em `du` dias úteis.

    `taxa` segue o significado do indexador: % a.a. no prefixado,
    % do CDI no pós-fixado e spread % a.a. em Selic e IPCA.
    """
    taxa = taxa / 100
    match indexador:
        case Indexador.PREFIXADO:
            return _fator_anual(taxa, du)
        case Indexador.CDI:
            cdi_dia = (_fator_anual(premissas.cdi, 1) - 1).quantize(Decimal("0.00000001"))
            return (1 + cdi_dia * taxa) ** du
        case Indexador.SELIC:
            return _fator_anual(premissas.selic, du) * _fator_anual(taxa, du)
        case Indexador.IPCA:
            return _fator_anual(premissas.ipca, du) * _fator_anual(taxa, du)


def projetar(
    *,
    tipo: TipoTitulo,
    indexador: Indexador,
    taxa: Decimal,
    valor_aplicado: Decimal,
    data_aplicacao: date,
    data_vencimento: date,
    data_resgate: date,
    premissas: Premissas,
) -> Projecao:
    if data_resgate < data_aplicacao:
        raise ValueError("data de resgate anterior à data de aplicação")
    if data_resgate > data_vencimento:
        raise ValueError("data de resgate posterior ao vencimento")

    dias_corridos = (data_resgate - data_aplicacao).days
    du = dias_uteis_entre(data_aplicacao, data_resgate)

    valor_bruto = valor_aplicado * fator_correcao(indexador, taxa, du, premissas)
    rendimento = valor_bruto - valor_aplicado

    if tipo.isento_ir:
        iof = ir = aliq_ir = Decimal(0)
    else:
        iof = rendimento * aliquota_iof(dias_corridos)
        aliq_ir = aliquota_ir(dias_corridos)
        ir = (rendimento - iof) * aliq_ir

    valor_liquido = valor_bruto - iof - ir

    def cents(v: Decimal) -> Decimal:
        return v.quantize(CENTAVO, rounding=ROUND_HALF_UP)

    def pct(v: Decimal) -> Decimal:
        return (v / valor_aplicado - 1).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    return Projecao(
        data_resgate=data_resgate,
        dias_corridos=dias_corridos,
        dias_uteis=du,
        valor_bruto=cents(valor_bruto),
        rendimento_bruto=cents(rendimento),
        iof=cents(iof),
        ir=cents(ir),
        aliquota_ir=aliq_ir,
        valor_liquido=cents(valor_liquido),
        rentabilidade_bruta=pct(valor_bruto),
        rentabilidade_liquida=pct(valor_liquido),
    )
