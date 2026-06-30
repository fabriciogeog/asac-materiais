from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth
from app.database import get_db
from app.deps import require_perfil
from app.models.usuario import PerfilEnum, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

_admin = require_perfil(PerfilEnum.ADMINISTRADOR)


@router.get("/", response_model=list[UsuarioResponse])
def listar(_: Usuario = Depends(_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).all()


@router.get("/{id}", response_model=UsuarioResponse)
def buscar(id: int, _: Usuario = Depends(_admin), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCreate, _: Usuario = Depends(_admin), db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.login == dados.login).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login já em uso")
    novo = Usuario(
        nome=dados.nome,
        login=dados.login,
        senhaHash=auth.criar_hash(dados.senha),
        perfil=dados.perfil.value,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{id}", response_model=UsuarioResponse)
def alterar(id: int, dados: UsuarioUpdate, _: Usuario = Depends(_admin), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(usuario, campo, valor.value if hasattr(valor, "value") else valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar(id: int, _: Usuario = Depends(_admin), db: Session = Depends(get_db)):
    """Desativa o usuário sem excluir o registro (RN-04)."""
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    usuario.usuarioAtivo = False
    db.commit()
