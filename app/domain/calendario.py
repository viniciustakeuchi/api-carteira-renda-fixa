"""Calendário de dias úteis no padrão ANBIMA (feriados nacionais)."""

from datetime import date, timedelta
from functools import lru_cache


def pascoa(ano: int) -> date:
    """Data da Páscoa pelo algoritmo de Meeus/Jones/Butcher."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


@lru_cache(maxsize=256)
def feriados_nacionais(ano: int) -> frozenset[date]:
    """Feriados nacionais que fecham o mercado financeiro no ano."""
    p = pascoa(ano)
    fixos = [
        date(ano, 1, 1),  # Confraternização Universal
        date(ano, 4, 21),  # Tiradentes
        date(ano, 5, 1),  # Dia do Trabalho
        date(ano, 9, 7),  # Independência
        date(ano, 10, 12),  # Nossa Senhora Aparecida
        date(ano, 11, 2),  # Finados
        date(ano, 11, 15),  # Proclamação da República
        date(ano, 12, 25),  # Natal
    ]
    if ano >= 2024:
        fixos.append(date(ano, 11, 20))  # Consciência Negra (Lei 14.759/2023)
    moveis = [
        p - timedelta(days=48),  # Segunda de Carnaval
        p - timedelta(days=47),  # Terça de Carnaval
        p - timedelta(days=2),  # Sexta-feira Santa
        p + timedelta(days=60),  # Corpus Christi
    ]
    return frozenset(fixos + moveis)


def eh_dia_util(dia: date) -> bool:
    return dia.weekday() < 5 and dia not in feriados_nacionais(dia.year)


def dias_uteis_entre(inicio: date, fim: date) -> int:
    """Dias úteis no intervalo (inicio, fim], convenção usada no mercado (du/252).

    O dia de início não conta e o dia final conta, como na contagem da B3.
    """
    if fim <= inicio:
        return 0
    total = 0
    dia = inicio + timedelta(days=1)
    while dia <= fim:
        if eh_dia_util(dia):
            total += 1
        dia += timedelta(days=1)
    return total
