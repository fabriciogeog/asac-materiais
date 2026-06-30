# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YOLO-based barcode detection pipeline. Uses YOLOv2 (ultralytics) to detect barcodes in images/webcam, decodes them with pyzbar, and looks up products via the Cosmos Bluesoft GTIN API or a local SQLite database.

## Environment Setup

```bash
source .venv/bin/activate
```

All dependencies are pinned in `requirements.txt`. The venv includes PyTorch with CUDA 13 support.

## Running Scripts

```bash
# Train model (outputs to detect/train-N/weights/)
python treinar.py

# Validate trained model (mAP metrics)
python validar.py

# Run inference on a single image
python prever.py

# Real-time webcam detection
python visualizar.py

# Decode barcode from image with pyzbar (no YOLO needed)
python barcode.py

# Look up product info by GTIN via Cosmos API
python consulta_produto.py
```

## Architecture

The pipeline has two detection paths:

1. **YOLO detection** (`treinar.py` → `prever.py`/`visualizar.py`): Trains on the Roboflow dataset (`dataset/`), saves weights to `detect/train-N/weights/`. The active trained model is `detect/train-2/weights/best.pt`. Base pretrained model is `yolo26n.pt`.

2. **pyzbar decoding** (`barcode.py`): Direct barcode decoding from clear images, no ML needed. Used when the barcode is already cropped/visible.

After detecting a barcode, `consulta_produto.py` queries the Cosmos Bluesoft API (`https://api.cosmos.bluesoft.com.br/gtins/{gtin}.json`) with the decoded barcode string to fetch product metadata. The API key is in `.env` as `BLUE_SOFT_COSMOS_KEY`.

## Dataset

Roboflow project `barcode-detect-02tkz` (version 5), single class `barcode`. Layout:
- `dataset/data.yaml` — YOLO dataset config
- `dataset/train/`, `dataset/valid/`, `dataset/test/` — images + YOLO-format labels

## Local Database

`produtos.sqlite3` stores product records with schema:
```sql
produtos(idProduto INTEGER PK AUTOINCREMENT, descricaoProd TEXT, marca TEXT, codBarras TEXT)
```

## Key Config

- `.env` holds `BLUE_SOFT_COSMOS_KEY` — load it before calling `consulta_produto.py` (the script currently hardcodes a token; it should use this env var instead)
- Training output directory is controlled by ultralytics' `project`/`name` params (defaults to `detect/`)
- Image size for training/inference: 640px
