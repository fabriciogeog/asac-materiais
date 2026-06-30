import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class TipoMovEnum(str, enum.Enum):
    ENTRADA  = "ENTRADA"
    SAIDA    = "SAIDA"
    AJUSTE   = "AJUSTE"
    DESCARTE = "DESCARTE"


class Movimentacao(Base):
    __tablename__ = "movimentacao"

    idMovimentacao = Column(Integer,  primary_key=True, autoincrement=True)
    tipoMov        = Column(String,   nullable=False)  # valores em TipoMovEnum
    dataMov        = Column(DateTime, nullable=False, default=datetime.now)
    quantMov       = Column(Numeric,  nullable=False)
    idProduto      = Column(Integer,  ForeignKey("produto.idProduto"),  nullable=False)
    idUsuario      = Column(Integer,  ForeignKey("usuario.idUsuario"),  nullable=False)
    observacao     = Column(String)

    produto  = relationship("Produto",  back_populates="movimentacoes")
    usuario  = relationship("Usuario",  back_populates="movimentacoes")
