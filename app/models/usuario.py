import enum
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from app.database import Base


class PerfilEnum(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERADOR      = "OPERADOR"
    CONSULTA      = "CONSULTA"


class Usuario(Base):
    __tablename__ = "usuario"

    idUsuario    = Column(Integer, primary_key=True, autoincrement=True)
    nome         = Column(String,  nullable=False)
    login        = Column(String,  nullable=False, unique=True)
    senhaHash    = Column(String,  nullable=False)
    perfil       = Column(String,  nullable=False)  # valores em PerfilEnum
    usuarioAtivo = Column(Boolean, nullable=False, default=True)
    dataCadastro = Column(Date,    nullable=False, default=date.today)

    movimentacoes = relationship("Movimentacao", back_populates="usuario")
