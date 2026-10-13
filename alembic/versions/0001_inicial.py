"""Tabelas de usuários e investimentos.

Revision ID: 0001
Revises:
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIPOS = ("CDB", "LCI", "LCA", "TESOURO_SELIC", "TESOURO_PREFIXADO", "TESOURO_IPCA")
INDEXADORES = ("PREFIXADO", "CDI", "SELIC", "IPCA")


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "investimentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("emissor", sa.String(120), nullable=False),
        sa.Column("tipo", sa.Enum(*TIPOS, name="tipo_titulo"), nullable=False),
        sa.Column("indexador", sa.Enum(*INDEXADORES, name="indexador"), nullable=False),
        sa.Column("taxa", sa.Numeric(9, 4), nullable=False),
        sa.Column("valor_aplicado", sa.Numeric(16, 2), nullable=False),
        sa.Column("data_aplicacao", sa.Date(), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_investimentos_usuario_id", "investimentos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_investimentos_usuario_id", "investimentos")
    op.drop_table("investimentos")
    op.drop_index("ix_usuarios_email", "usuarios")
    op.drop_table("usuarios")
    sa.Enum(name="indexador").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_titulo").drop(op.get_bind(), checkfirst=True)
