/* ============================================================
   barcode-scanner.js — Scanner contínuo de código de barras
   Uso: abrirScannerModal(callback)
   Callback recebe o objeto de /barcode/lookup/{codigo}
   ============================================================ */

(function () {
  let _stream    = null;
  let _modal     = null;
  let _callback  = null;
  let _scanTimer = null;
  let _ativo     = false;

  function _criarModal() {
    const el = document.createElement('div');
    el.id = 'modal-scanner';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-labelledby', 'scanner-titulo');
    el.className = 'modal-overlay';
    el.innerHTML = `
      <div class="modal-caixa">
        <h3 id="scanner-titulo">Escanear código de barras</h3>
        <div class="campo" id="scanner-camera-campo" hidden>
          <label for="scanner-camera">Câmera</label>
          <select id="scanner-camera" aria-label="Selecionar câmera"></select>
        </div>
        <div class="scanner-video-wrapper">
          <video id="scanner-video" autoplay playsinline
                 aria-label="Pré-visualização da câmera"></video>
          <div class="scanner-mira" aria-hidden="true"></div>
        </div>
        <div id="scanner-status" role="status" aria-live="polite"
             class="scanner-status scanner-buscando">
          Posicione o código de barras na câmera…
        </div>
        <div class="acoes-formulario">
          <button id="scanner-btn-fechar" class="btn btn-secundario">Cancelar</button>
        </div>
        <canvas id="scanner-canvas" hidden></canvas>
      </div>
    `;
    document.body.appendChild(el);
    return el;
  }

  /* ── Câmera ──────────────────────────────────────────────── */

  async function _iniciarCamera(deviceId = null) {
    if (_stream) {
      _stream.getTracks().forEach(t => t.stop());
      _stream = null;
    }
    const constraints = {
      video: deviceId
        ? { deviceId: { exact: deviceId }, width: { ideal: 1280 } }
        : { width: { ideal: 1280 } },
    };
    _stream = await navigator.mediaDevices.getUserMedia(constraints);
    document.getElementById('scanner-video').srcObject = _stream;
    return _stream.getVideoTracks()[0].getSettings().deviceId;
  }

  async function _popularSeletorCameras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter(d => d.kind === 'videoinput');
    const sel     = document.getElementById('scanner-camera');
    const campo   = document.getElementById('scanner-camera-campo');

    sel.innerHTML = cameras
      .map((cam, i) =>
        `<option value="${cam.deviceId}">${cam.label || `Câmera ${i + 1}`}</option>`)
      .join('');

    if (cameras.length > 1) {
      campo.removeAttribute('hidden');
      sel.selectedIndex = cameras.length - 1; // USB externa fica por último
    } else {
      campo.setAttribute('hidden', '');
    }
    return sel.value;
  }

  /* ── Loop de escaneamento ────────────────────────────────── */

  function _iniciarLoop() {
    _ativo = true;
    _executarCiclo();
  }

  function _pararLoop() {
    _ativo = false;
    if (_scanTimer) { clearTimeout(_scanTimer); _scanTimer = null; }
  }

  async function _executarCiclo() {
    if (!_ativo || !_stream) return;

    const video  = document.getElementById('scanner-video');
    const canvas = document.getElementById('scanner-canvas');

    if (!video || video.readyState < video.HAVE_ENOUGH_DATA) {
      _scanTimer = setTimeout(_executarCiclo, 200);
      return;
    }

    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    await new Promise(resolve => {
      canvas.toBlob(async (blob) => {
        if (!_ativo) { resolve(); return; }
        try {
          const form = new FormData();
          form.append('file', blob, 'frame.jpg');
          const { codigo } = await api.postForm('/barcode/scan', form);

          // Barcode detectado — para o loop e processa
          _pararLoop();
          await _processar(codigo);
        } catch (err) {
          if (err.status !== 404) {
            // Erro inesperado (rede, servidor) — mostra e para
            _pararLoop();
            _setStatus(err.message, false);
          }
          // 404 = frame sem barcode → continua normalmente
        }
        resolve();
      }, 'image/jpeg', 0.88);
    });

    if (_ativo) {
      _scanTimer = setTimeout(_executarCiclo, 350);
    }
  }

  async function _processar(codigo) {
    _setStatus(`Código detectado: ${codigo} — consultando…`, false);
    try {
      const resultado = await api.get(`/barcode/lookup/${encodeURIComponent(codigo)}`);
      _fechar();
      _callback(resultado);
    } catch (err) {
      _setStatus(`Erro ao consultar produto: ${err.message}`, false);
    }
  }

  /* ── UI helpers ──────────────────────────────────────────── */

  function _setStatus(texto, buscando = true) {
    const el = document.getElementById('scanner-status');
    if (!el) return;
    el.textContent = texto;
    el.className = 'scanner-status' + (buscando ? ' scanner-buscando' : '');
  }

  function _fechar() {
    _pararLoop();
    if (_stream) { _stream.getTracks().forEach(t => t.stop()); _stream = null; }
    if (_modal)  { _modal.style.display = 'none'; }
    document.removeEventListener('keydown', _onKeyDown);
  }

  function _onKeyDown(e) { if (e.key === 'Escape') _fechar(); }

  /* ── API pública ─────────────────────────────────────────── */

  async function abrirScannerModal(callback) {
    _callback = callback;
    if (!_modal) _modal = _criarModal();

    _setStatus('Posicione o código de barras na câmera…');
    document.getElementById('scanner-btn-fechar').onclick = _fechar;
    _modal.style.display = 'flex';

    try {
      const activeId      = await _iniciarCamera();
      const preferredId   = await _popularSeletorCameras();
      if (preferredId && preferredId !== activeId) {
        await _iniciarCamera(preferredId);
      }
      document.getElementById('scanner-camera').onchange = async function () {
        _pararLoop();
        try {
          await _iniciarCamera(this.value);
          _iniciarLoop();
        } catch {
          _setStatus('Não foi possível trocar de câmera.', false);
        }
      };
    } catch {
      _setStatus('Câmera não disponível. Verifique as permissões do navegador.', false);
      return;
    }

    document.getElementById('scanner-btn-fechar').focus();
    document.addEventListener('keydown', _onKeyDown);
    _iniciarLoop();
  }

  window.abrirScannerModal = abrirScannerModal;
})();
