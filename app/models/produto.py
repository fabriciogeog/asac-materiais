from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Produto(Base):
    __tablename__ = "produto"

    idProduto     = Column(Integer,  primary_key=True, autoincrement=True)
    codBarras     = Column(String,   unique=True)
    descricao     = Column(String,   nullable=False)
    marca         = Column(String)
    idCategoria   = Column(Integer,  ForeignKey("categoria.idCategoria"), nullable=False)
    estoqueMinimo = Column(Numeric,  nullable=False, default=0)
    saldoAtual    = Column(Numeric,  nullable=False, default=0)
    produtoAtivo  = Column(Boolean,  nullable=False, default=True)
    dataCadastro  = Column(Date,     nullable=False, default=date.today)

    categoria     = relationship("Categoria",    back_populates="produtos")
    movimentacoes = relationship("Movimentacao", back_populates="produto")
