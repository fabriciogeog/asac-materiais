from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Categoria(Base):
    __tablename__ = "categoria"

    idCategoria = Column(Integer, primary_key=True, autoincrement=True)
    nome        = Column(String, nullable=False, unique=True)
    descricao   = Column(String)

    produtos = relationship("Produto", back_populates="categoria")
