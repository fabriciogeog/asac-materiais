from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_perfil
from app.models.produto import Produto
from app.models.usuario import PerfilEnum, Usuario
from app.schemas.produto import ProdutoCreate, ProdutoResponse, ProdutoUpdate

router = APIRouter(prefix="/produtos", tags=["Produtos"])

_gestao = require_perfil(PerfilEnum.ADMINISTRADOR, PerfilEnum.OPERADOR)


@router.get("/", response_model=list[ProdutoResponse])
def listar(
    apenas_ativos: bool = Query(True, description="Filtrar apenas produtos ativos"),
    _: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Produto)
    if apenas_ativos:
        q = q.filter(Produto.produtoAtivo == True)
    return q.all()


@router.get("/abaixo-minimo", response_model=list[ProdutoResponse])
def abaixo_do_minimo(_: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna produtos com saldoAtual < estoqueMinimo (alerta de reposição)."""
    return (
        db.query(Produto)
        .filter(Produto.produtoAtivo == True, Produto.saldoAtual < Produto.estoqueMinimo)
        .all()
    )


@router.get("/{id}", response_model=ProdutoResponse)
def buscar(id: int, _: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return produto


@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def incluir(dados: ProdutoCreate, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    if dados.codBarras and db.query(Produto).filter(Produto.codBarras == dados.codBarras).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de barras já cadastrado")
    novo = Produto(**dados.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{id}", response_model=ProdutoResponse)
def alterar(id: int, dados: ProdutoUpdate, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar(id: int, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    """Soft delete: marca o produto como inativo (RF-01c)."""
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    produto.produtoAtivo = False
    db.commit()
