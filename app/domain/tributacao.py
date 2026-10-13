"""IR regressivo e IOF sobre rendimentos de renda fixa (pessoa física)."""

from decimal import Decimal

# Alíquota de IOF por dia corrido (1 a 29) desde a aplicação, em % do rendimento.
_TABELA_IOF = (
    96, 93, 90, 86, 83, 80, 76, 73, 70, 66,
    63, 60, 56, 53, 50, 46, 43, 40, 36, 33,
    30, 26, 23, 20, 16, 13, 10, 6, 3,
)  # fmt: skip


def aliquota_iof(dias_corridos: int) -> Decimal:
    if dias_corridos >= 30:
        return Decimal("0")
    dia = max(dias_corridos, 1)
    return Decimal(_TABELA_IOF[dia - 1]) / 100


def aliquota_ir(dias_corridos: int) -> Decimal:
    """Tabela regressiva da Lei 11.033/2004."""
    if dias_corridos <= 180:
        return Decimal("0.225")
    if dias_corridos <= 360:
        return Decimal("0.20")
    if dias_corridos <= 720:
        return Decimal("0.175")
    return Decimal("0.15")
