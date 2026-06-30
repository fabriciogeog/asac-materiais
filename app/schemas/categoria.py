from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nome: str
    descricao: str | None = None


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None


class CategoriaResponse(BaseModel):
    idCategoria: int
    nome: str
    descricao: str | None

    model_config = {"from_attributes": True}
