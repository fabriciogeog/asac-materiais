#!/usr/bin/env bash
# Gera /etc/systemd/system/asac.service a partir de asac.service.template,
# preenchendo caminho do projeto e usuário/grupo atuais. Evita caminhos
# hardcoded que quebram quando o projeto é clonado em outra pasta/máquina.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_USER="${SUDO_USER:-$(whoami)}"
RUN_GROUP="$(id -gn "$RUN_USER")"

TEMPLATE="$SCRIPT_DIR/asac.service.template"
TARGET="/etc/systemd/system/asac.service"

if [ ! -f "$PROJECT_DIR/.venv/bin/uvicorn" ]; then
    echo "Aviso: $PROJECT_DIR/.venv/bin/uvicorn não existe." >&2
    echo "Crie o venv antes de instalar o serviço (veja o passo 0 do README)." >&2
    exit 1
fi

sed \
    -e "s#__PROJECT_DIR__#$PROJECT_DIR#g" \
    -e "s#__USER__#$RUN_USER#g" \
    -e "s#__GROUP__#$RUN_GROUP#g" \
    "$TEMPLATE" | sudo tee "$TARGET" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable --now asac

echo "Serviço instalado: PROJECT_DIR=$PROJECT_DIR USER=$RUN_USER GROUP=$RUN_GROUP"
