from datetime import date
from pydantic import BaseModel, field_validator
from app.models.usuario import PerfilEnum


class UsuarioCreate(BaseModel):
    nome: str
    login: str
    senha: str  # texto simples — será convertido em hash no router
    perfil: PerfilEnum

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter ao menos 8 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    perfil: PerfilEnum | None = None
    senha: str | None = None

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("A senha deve ter ao menos 8 caracteres")
        return v


class UsuarioResponse(BaseModel):
    idUsuario: int
    nome: str
    login: str
    perfil: PerfilEnum
    usuarioAtivo: bool
    dataCadastro: date

    model_config = {"from_attributes": True}
