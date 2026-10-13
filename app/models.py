from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain.tipos import Indexador, TipoTitulo


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    investimentos: Mapped[list["Investimento"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Investimento(Base):
    __tablename__ = "investimentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(120))
    emissor: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[TipoTitulo] = mapped_column(Enum(TipoTitulo, name="tipo_titulo"))
    indexador: Mapped[Indexador] = mapped_column(Enum(Indexador, name="indexador"))
    taxa: Mapped[Decimal] = mapped_column(Numeric(9, 4))
    valor_aplicado: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    data_aplicacao: Mapped[date] = mapped_column(Date)
    data_vencimento: Mapped[date] = mapped_column(Date)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped[Usuario] = relationship(back_populates="investimentos")
