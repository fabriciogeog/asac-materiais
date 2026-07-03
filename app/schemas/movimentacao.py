from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.movimentacao import TipoMovEnum


class MovimentacaoCreate(BaseModel):
    tipoMov: TipoMovEnum
    quantMov: Decimal
    idProduto: int
    observacao: str | None = None

    @field_validator("quantMov")
    @classmethod
    def quantidade_positiva(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantMov deve ser maior que zero")
        return v


class MovimentacaoResponse(BaseModel):
    idMovimentacao: int
    tipoMov: TipoMovEnum
    dataMov: datetime
    quantMov: Decimal
    idProduto: int
    idUsuario: int
    observacao: str | None

    model_config = {"from_attributes": True}


class MovimentacaoPagina(BaseModel):
    itens: list[MovimentacaoResponse]
    total: int
    pagina: int
    tamanho: int
    totalPaginas: int
