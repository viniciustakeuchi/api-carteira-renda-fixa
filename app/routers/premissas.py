from decimal import Decimal
from typing import Annotated

from fastapi import Depends, Query

from app.config import settings
from app.domain.rentabilidade import Premissas

TaxaAnual = Annotated[Decimal | None, Query(ge=-50, le=100, description="% ao ano")]


def premissas_query(
    cdi: TaxaAnual = None, selic: TaxaAnual = None, ipca: TaxaAnual = None
) -> Premissas:
    """Premissas da requisição, em fração; as omitidas vêm da configuração."""
    return Premissas(
        cdi=(cdi if cdi is not None else settings.cdi_anual) / 100,
        selic=(selic if selic is not None else settings.selic_anual) / 100,
        ipca=(ipca if ipca is not None else settings.ipca_anual) / 100,
    )


PremissasDep = Annotated[Premissas, Depends(premissas_query)]
