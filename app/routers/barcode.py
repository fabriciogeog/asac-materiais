import io
import logging
import os
import pathlib

import numpy as np
import requests
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from pyzbar.pyzbar import decode
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.produto import Produto
from app.models.usuario import Usuario

router = APIRouter(prefix="/barcode", tags=["Barcode"])

_logger = logging.getLogger(__name__)
_COSMOS_URL = "https://api.cosmos.bluesoft.com.br/gtins/{gtin}.json"
_MODEL_PATH = pathlib.Path("detect/train-2/weights/best.pt")
_yolo = None


def _get_yolo():
    global _yolo
    if _yolo is None and _MODEL_PATH.exists():
        from ultralytics import YOLO
        _yolo = YOLO(str(_MODEL_PATH))
        _logger.info("Modelo YOLO carregado: %s", _MODEL_PATH)
    return _yolo


def _decodificar(img: Image.Image) -> str | None:
    """Pipeline YOLO → crop → PyZbar; fallback para PyZbar no frame completo."""
    model = _get_yolo()
    if model is not None:
        img_np = np.array(img.convert("RGB"))
        for r in model(img_np, verbose=False):
            for box in r.boxes.xyxy.tolist():
                x1, y1, x2, y2 = map(int, box)
                m = 20
                h, w = img_np.shape[:2]
                crop = img.crop((max(0, x1 - m), max(0, y1 - m),
                                 min(w, x2 + m), min(h, y2 + m)))
                found = decode(crop)
                if found:
                    return found[0].data.decode("utf-8")

    found = decode(img)
    return found[0].data.decode("utf-8") if found else None


@router.post("/scan")
def scan(
    file: UploadFile = File(...),
    _: Usuario = Depends(get_current_user),
):
    """Detecta e decodifica código de barras via YOLO + PyZbar (RN-01)."""
    try:
        img = Image.open(io.BytesIO(file.file.read()))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Imagem inválida")

    codigo = _decodificar(img)
    if not codigo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum código detectado na imagem",
        )
    return {"codigo": codigo}


@router.get("/lookup/{codigo}")
def lookup(
    codigo: str,
    _: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca produto local; consulta Cosmos API se não encontrado (RF-03)."""
    produto = db.query(Produto).filter(Produto.codBarras == codigo).first()
    if produto:
        return {
            "encontrado_local": True,
            "idProduto": produto.idProduto,
            "descricao": produto.descricao,
            "marca": produto.marca,
            "saldoAtual": float(produto.saldoAtual),
            "produtoAtivo": produto.produtoAtivo,
            "codBarras": produto.codBarras,
        }

    cosmos = _consultar_cosmos(codigo)
    return {
        "encontrado_local": False,
        "descricao": cosmos.get("description", ""),
        "marca": (cosmos.get("brand") or {}).get("name", ""),
        "codBarras": codigo,
    }


def _consultar_cosmos(gtin: str) -> dict:
    token = os.getenv("BLUE_SOFT_COSMOS_KEY", "")
    if not token:
        _logger.warning("BLUE_SOFT_COSMOS_KEY não configurada")
        return {}
    try:
        r = requests.get(
            _COSMOS_URL.format(gtin=gtin),
            headers={
                "X-Cosmos-Token": token,
                "Content-Type": "application/json",
                "User-Agent": "Cosmos-API-Request",
            },
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        _logger.warning("Cosmos API retornou %s para GTIN %s", r.status_code, gtin)
    except Exception as exc:
        _logger.error("Erro ao consultar Cosmos API: %s", exc)
    return {}
