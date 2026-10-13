from enum import StrEnum


class TipoTitulo(StrEnum):
    CDB = "CDB"
    LCI = "LCI"
    LCA = "LCA"
    TESOURO_SELIC = "TESOURO_SELIC"
    TESOURO_PREFIXADO = "TESOURO_PREFIXADO"
    TESOURO_IPCA = "TESOURO_IPCA"

    @property
    def isento_ir(self) -> bool:
        """LCI e LCA são isentas de IR e IOF para pessoa física."""
        return self in {TipoTitulo.LCI, TipoTitulo.LCA}


class Indexador(StrEnum):
    PREFIXADO = "PREFIXADO"  # taxa = % ao ano
    CDI = "CDI"  # taxa = % do CDI (ex.: 110 para 110% do CDI)
    SELIC = "SELIC"  # taxa = spread % ao ano sobre a Selic
    IPCA = "IPCA"  # taxa = spread % ao ano sobre o IPCA
