from decimal import Decimal
from datetime import date
from pydantic import BaseModel, field_validator


class ProdutoCreate(BaseModel):
    codBarras: str | None = None
    descricao: str
    marca: str | None = None
    idCategoria: int
    estoqueMinimo: Decimal = Decimal("0")

    @field_validator("estoqueMinimo")
    @classmethod
    def estoque_nao_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("estoqueMinimo não pode ser negativo")
        return v


class ProdutoUpdate(BaseModel):
    codBarras: str | None = None
    descricao: str | None = None
    marca: str | None = None
    idCategoria: int | None = None
    estoqueMinimo: Decimal | None = None


class ProdutoResponse(BaseModel):
    idProduto: int
    codBarras: str | None
    descricao: str
    marca: str | None
    idCategoria: int
    estoqueMinimo: Decimal
    saldoAtual: Decimal
    produtoAtivo: bool
    dataCadastro: date

    model_config = {"from_attributes": True}
