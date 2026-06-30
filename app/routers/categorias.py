from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_perfil
from app.models.categoria import Categoria
from app.models.usuario import PerfilEnum, Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["Categorias"])

_gestao = require_perfil(PerfilEnum.ADMINISTRADOR, PerfilEnum.OPERADOR)


@router.get("/", response_model=list[CategoriaResponse])
def listar(_: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Categoria).all()


@router.get("/{id}", response_model=CategoriaResponse)
def buscar(id: int, _: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    categoria = db.get(Categoria, id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return categoria


@router.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def incluir(dados: CategoriaCreate, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    if db.query(Categoria).filter(Categoria.nome == dados.nome).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma categoria com esse nome")
    nova = Categoria(**dados.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router.put("/{id}", response_model=CategoriaResponse)
def alterar(id: int, dados: CategoriaUpdate, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    categoria = db.get(Categoria, id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(id: int, _: Usuario = Depends(_gestao), db: Session = Depends(get_db)):
    categoria = db.get(Categoria, id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    if categoria.produtos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir: existem produtos nessa categoria",
        )
    db.delete(categoria)
    db.commit()
