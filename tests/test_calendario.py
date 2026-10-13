from datetime import date

import pytest

from app.domain.calendario import dias_uteis_entre, eh_dia_util, feriados_nacionais, pascoa


@pytest.mark.parametrize(
    ("ano", "esperado"),
    [(2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5))],
)
def test_pascoa(ano: int, esperado: date) -> None:
    assert pascoa(ano) == esperado


def test_feriados_moveis_2026() -> None:
    feriados = feriados_nacionais(2026)
    assert date(2026, 2, 16) in feriados  # segunda de Carnaval
    assert date(2026, 2, 17) in feriados  # terça de Carnaval
    assert date(2026, 4, 3) in feriados  # Sexta-feira Santa
    assert date(2026, 6, 4) in feriados  # Corpus Christi


def test_consciencia_negra_so_a_partir_de_2024() -> None:
    assert date(2023, 11, 20) not in feriados_nacionais(2023)
    assert date(2024, 11, 20) in feriados_nacionais(2024)


def test_fim_de_semana_e_feriado_nao_sao_uteis() -> None:
    assert not eh_dia_util(date(2026, 10, 10))  # sábado
    assert not eh_dia_util(date(2026, 10, 12))  # Nossa Senhora Aparecida, segunda
    assert eh_dia_util(date(2026, 10, 13))


def test_dias_uteis_exclui_inicio_e_inclui_fim() -> None:
    # Seg 05/10/2026 a seg 12/10/2026 (feriado): ter, qua, qui, sex = 4
    assert dias_uteis_entre(date(2026, 10, 5), date(2026, 10, 12)) == 4
    assert dias_uteis_entre(date(2026, 10, 5), date(2026, 10, 13)) == 5


def test_dias_uteis_intervalo_vazio() -> None:
    assert dias_uteis_entre(date(2026, 10, 13), date(2026, 10, 13)) == 0
    assert dias_uteis_entre(date(2026, 10, 13), date(2026, 10, 1)) == 0


def test_dias_uteis_ano_2025() -> None:
    # 261 dias de semana menos 9 feriados em dias de semana.
    assert dias_uteis_entre(date(2024, 12, 31), date(2025, 12, 31)) == 252
