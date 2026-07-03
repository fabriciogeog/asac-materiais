import math
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_perfil
from app.models.movimentacao import Movimentacao, TipoMovEnum
from app.models.produto import Produto
from app.models.usuario import PerfilEnum, Usuario
from app.schemas.movimentacao import MovimentacaoCreate, MovimentacaoPagina, MovimentacaoResponse

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])

_gestao = require_perfil(PerfilEnum.ADMINISTRADOR, PerfilEnum.OPERADOR)

_SAIDA = {TipoMovEnum.SAIDA, TipoMovEnum.DESCARTE}


@router.get("/", response_model=MovimentacaoPagina)
def listar(
    idProduto: int | None = Query(None, description="Filtrar por produto"),
    idUsuario: int | None = Query(None, description="Filtrar por usuário"),
    dataInicio: date | None = Query(None, description="Filtrar a partir desta data (inclusive)"),
    dataFim: date | None = Query(None, description="Filtrar até esta data (inclusive)"),
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    _: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Movimentacao)
    if idProduto:
        q = q.filter(Movimentacao.idProduto == idProduto)
    if idUsuario:
        q = q.filter(Movimentacao.idUsuario == idUsuario)
    if dataInicio:
        q = q.filter(Movimentacao.dataMov >= datetime.combine(dataInicio, time.min))
    if dataFim:
        q = q.filter(Movimentacao.dataMov <= datetime.combine(dataFim, time.max))

    total = q.count()
    itens = (
        q.order_by(Movimentacao.dataMov.desc(), Movimentacao.idMovimentacao.desc())
        .offset((pagina - 1) * tamanho)
        .limit(tamanho)
        .all()
    )
    return MovimentacaoPagina(
        itens=itens,
        total=total,
        pagina=pagina,
        tamanho=tamanho,
        totalPaginas=math.ceil(total / tamanho) if total else 0,
    )


@router.get("/{id}", response_model=MovimentacaoResponse)
def buscar(id: int, _: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    mov = db.get(Movimentacao, id)
    if not mov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada")
    return mov


@router.post("/", response_model=MovimentacaoResponse, status_code=status.HTTP_201_CREATED)
def inserir(
    dados: MovimentacaoCreate,
    usuario_logado: Usuario = Depends(_gestao),
    db: Session = Depends(get_db),
):
    produto = db.get(Produto, dados.idProduto)
    if not produto or not produto.produtoAtivo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado ou inativo")

    if dados.tipoMov in _SAIDA and produto.saldoAtual < dados.quantMov:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Saldo insuficiente: disponível {float(produto.saldoAtual):g}, solicitado {float(dados.quantMov):g}",
        )

    if dados.tipoMov in _SAIDA:
        produto.saldoAtual -= dados.quantMov
    else:
        produto.saldoAtual += dados.quantMov

    nova_mov = Movimentacao(
        **dados.model_dump(),
        idUsuario=usuario_logado.idUsuario,  # preenchido pelo token, não pelo cliente
    )
    db.add(nova_mov)
    db.commit()
    db.refresh(nova_mov)
    return nova_mov
