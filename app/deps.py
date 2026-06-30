from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app import auth
from app.database import get_db
from app.models.usuario import PerfilEnum, Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.decodificar_token(token)
        id_usuario = payload.get("sub")
        if id_usuario is None:
            raise erro_credenciais
    except JWTError:
        raise erro_credenciais

    usuario = db.get(Usuario, int(id_usuario))
    if not usuario or not usuario.usuarioAtivo:
        raise erro_credenciais
    return usuario


def require_perfil(*perfis: PerfilEnum):
    """Dependência de autorização por perfil.

    Uso: Depends(require_perfil(PerfilEnum.ADMINISTRADOR, PerfilEnum.OPERADOR))
    """
    valores = {p.value for p in perfis}

    def verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in valores:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfis permitidos: {sorted(valores)}",
            )
        return usuario

    return verificar
