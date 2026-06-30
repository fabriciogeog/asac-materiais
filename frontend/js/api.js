/* ============================================================
   api.js — Wrapper de chamadas à API com suporte a JWT
   ============================================================ */

const API_BASE = '';  // mesma origem (servido pelo FastAPI em /ui)

function getToken() {
    return sessionStorage.getItem('asac_token');
}

function getPerfil() {
    return sessionStorage.getItem('asac_perfil');
}

function salvarSessao(token) {
    sessionStorage.setItem('asac_token', token);
    // Decodifica payload do JWT (base64url → JSON) para obter o perfil
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    sessionStorage.setItem('asac_perfil', payload.perfil);
    sessionStorage.setItem('asac_usuario_id', payload.sub);
}

function encerrarSessao() {
    sessionStorage.removeItem('asac_token');
    sessionStorage.removeItem('asac_perfil');
    sessionStorage.removeItem('asac_usuario_id');
}

function cabecalhos(isForm = false) {
    const h = {};
    const token = getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    if (!isForm) h['Content-Type'] = 'application/json';
    return h;
}

async function apiFetch(caminho, opcoes = {}) {
    const isForm = opcoes.body instanceof URLSearchParams;
    let resp;
    try {
        resp = await fetch(API_BASE + caminho, {
            ...opcoes,
            headers: { ...cabecalhos(isForm), ...(opcoes.headers || {}) },
        });
    } catch {
        throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão.');
    }

    if (resp.status === 401) {
        encerrarSessao();
        window.location.href = '/ui/login.html';
        return;
    }

    if (resp.status === 204) return null;

    const dados = await resp.json();
    if (!resp.ok) {
        const msg = Array.isArray(dados.detail)
            ? dados.detail.map(e => e.msg).join('; ')
            : (dados.detail || 'Erro desconhecido');
        throw new Error(msg);
    }
    return dados;
}

const api = {
    get:      (caminho)       => apiFetch(caminho),
    post:     (caminho, body) => apiFetch(caminho, { method: 'POST', body: JSON.stringify(body) }),
    postForm: (caminho, body) => apiFetch(caminho, { method: 'POST', body }),
    put:      (caminho, body) => apiFetch(caminho, { method: 'PUT',  body: JSON.stringify(body) }),
    delete:   (caminho)       => apiFetch(caminho, { method: 'DELETE' }),
};
