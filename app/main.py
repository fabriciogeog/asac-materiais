from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, categorias, movimentacoes, produtos, usuarios

app = FastAPI(
    title="ASAC — Controle de Materiais de Consumo",
    description="API para gestão de entradas, saídas e consultas de materiais.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(produtos.router)
app.include_router(usuarios.router)
app.include_router(movimentacoes.router)

app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/", tags=["Status"])
def raiz():
    return {"status": "online", "sistema": "ASAC Materiais v0.1"}
