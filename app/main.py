from fastapi import FastAPI

from app.routers import auth, carteira, investimentos

app = FastAPI(
    title="API de Carteira de Renda Fixa",
    description=(
        "Cadastro de títulos de renda fixa (CDB, LCI, LCA e Tesouro Direto) e projeção de "
        "rentabilidade bruta e líquida, com dias úteis ANBIMA, IR regressivo e IOF."
    ),
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(investimentos.router)
app.include_router(carteira.router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
