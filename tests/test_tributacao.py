from decimal import Decimal

import pytest

from app.domain.tributacao import aliquota_iof, aliquota_ir


@pytest.mark.parametrize(
    ("dias", "aliquota"),
    [(0, "0.225"), (180, "0.225"), (181, "0.20"), (360, "0.20"), (361, "0.175"),
     (720, "0.175"), (721, "0.15"), (2000, "0.15")],
)  # fmt: skip
def test_ir_regressivo(dias: int, aliquota: str) -> None:
    assert aliquota_ir(dias) == Decimal(aliquota)


@pytest.mark.parametrize(
    ("dias", "aliquota"),
    [(0, "0.96"), (1, "0.96"), (15, "0.50"), (29, "0.03"), (30, "0"), (400, "0")],
)
def test_iof_regressivo(dias: int, aliquota: str) -> None:
    assert aliquota_iof(dias) == Decimal(aliquota)
