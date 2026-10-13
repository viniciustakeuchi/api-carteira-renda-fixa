from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.tipos import Indexador, TipoTitulo

# Títulos do Tesouro só existem com um indexador.
_INDEXADOR_TESOURO = {
    TipoTitulo.TESOURO_SELIC: Indexador.SELIC,
    TipoTitulo.TESOURO_PREFIXADO: Indexador.PREFIXADO,
    TipoTitulo.TESOURO_IPCA: Indexador.IPCA,
}


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InvestimentoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120, examples=["CDB Banco X 110% CDI"])
    emissor: str = Field(min_length=1, max_length=120, examples=["Banco X"])
    tipo: TipoTitulo
    indexador: Indexador
    taxa: Decimal = Field(
        gt=0,
        max_digits=9,
        decimal_places=4,
        description="% a.a. (prefixado), % do CDI (CDI) ou spread % a.a. (Selic e IPCA)",
        examples=[110],
    )
    valor_aplicado: Decimal = Field(gt=0, max_digits=16, decimal_places=2, examples=[10000])
    data_aplicacao: date
    data_vencimento: date

    @model_validator(mode="after")
    def validar(self) -> Self:
        if self.data_vencimento <= self.data_aplicacao:
            raise ValueError("data_vencimento deve ser posterior a data_aplicacao")
        esperado = _INDEXADOR_TESOURO.get(self.tipo)
        if esperado and self.indexador != esperado:
            raise ValueError(f"{self.tipo} usa o indexador {esperado}")
        if self.tipo not in _INDEXADOR_TESOURO and self.indexador == Indexador.SELIC:
            raise ValueError("indexador SELIC é exclusivo do Tesouro Selic")
        return self


class InvestimentoCriar(InvestimentoBase):
    pass


class InvestimentoSaida(InvestimentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProjecaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_resgate: date
    dias_corridos: int
    dias_uteis: int
    valor_bruto: Decimal
    rendimento_bruto: Decimal
    iof: Decimal
    ir: Decimal
    aliquota_ir: Decimal
    valor_liquido: Decimal
    rentabilidade_bruta: Decimal = Field(description="Fração: 0.12 = 12%")
    rentabilidade_liquida: Decimal = Field(description="Fração: 0.12 = 12%")


class PremissasSaida(BaseModel):
    cdi: Decimal
    selic: Decimal
    ipca: Decimal


class ProjecaoInvestimento(BaseModel):
    investimento: InvestimentoSaida
    premissas: PremissasSaida
    projecao: ProjecaoSaida


class TotalPorTipo(BaseModel):
    tipo: TipoTitulo
    valor_aplicado: Decimal
    valor_liquido: Decimal
    participacao: Decimal = Field(description="Fração do valor líquido da carteira")


class ResumoCarteira(BaseModel):
    data_referencia: date
    premissas: PremissasSaida
    quantidade: int
    valor_aplicado: Decimal
    valor_bruto: Decimal
    valor_liquido: Decimal
    impostos: Decimal
    por_tipo: list[TotalPorTipo]
