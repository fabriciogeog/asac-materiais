/* ============================================================
   app.js — Utilitários compartilhados: nav, notificações, auth
   ============================================================ */

/* ── Guard de autenticação ───────────────────────────────────── */
function exigirAuth() {
    if (!getToken()) {
        window.location.href = '/ui/login.html';
    }
}

function exigirPerfil(...perfisPermitidos) {
    exigirAuth();
    if (!perfisPermitidos.includes(getPerfil())) {
        window.location.href = '/ui/index.html';
    }
}

/* ── Logout ──────────────────────────────────────────────────── */
function logout() {
    encerrarSessao();
    window.location.href = '/ui/login.html';
}

/* ── Renderiza navegação principal ────────────────────────────── */
function renderizarNav(paginaAtual) {
    const perfil = getPerfil();
    const nav = document.getElementById('nav-principal');
    if (!nav) return;

    const itens = [
        { href: '/ui/index.html',      texto: 'Início',    pagina: 'index' },
        { href: '/ui/produtos.html',   texto: 'Produtos',  pagina: 'produtos' },
    ];

    if (perfil !== 'CONSULTA') {
        itens.push(
            { href: '/ui/movimentacoes.html', texto: 'Movimentações', pagina: 'movimentacoes' },
            { href: '/ui/categorias.html',    texto: 'Categorias',    pagina: 'categorias'    },
        );
    }

    // Relatórios são somente leitura: disponíveis para todos os perfis.
    itens.push({ href: '/ui/relatorios.html', texto: 'Relatórios', pagina: 'relatorios' });

    if (perfil === 'ADMINISTRADOR') {
        itens.push({ href: '/ui/usuarios.html', texto: 'Usuários', pagina: 'usuarios' });
    }

    nav.innerHTML = `
        <ul role="list">
            ${itens.map(i => `
                <li>
                    <a href="${i.href}"
                       ${i.pagina === paginaAtual ? 'aria-current="page"' : ''}>
                        ${i.texto}
                    </a>
                </li>
            `).join('')}
        </ul>
        <div class="nav-usuario">
            <span aria-label="Perfil do usuário">Perfil: <strong>${perfil}</strong></span>
            <button class="btn btn-secundario btn-sm" onclick="logout()">Sair</button>
        </div>
    `;
}

/* ── Notificações acessíveis ─────────────────────────────────── */
let _timerNotif = null;

function notificar(mensagem, tipo = 'sucesso') {
    const el = document.getElementById('notificacao');
    if (!el) return;

    el.textContent = mensagem;
    el.className = `notificacao notificacao-${tipo}`;
    el.removeAttribute('hidden');

    if (_timerNotif) clearTimeout(_timerNotif);
    _timerNotif = setTimeout(() => {
        el.setAttribute('hidden', '');
        el.className = 'notificacao oculto';
    }, 5000);
}

/* ── Helpers de UI ────────────────────────────────────────────── */
function mostrarElemento(id)  { document.getElementById(id)?.removeAttribute('hidden'); }
function ocultarElemento(id)  { document.getElementById(id)?.setAttribute('hidden', ''); }
function focarElemento(id)    { document.getElementById(id)?.focus(); }

function limparFormulario(formId) {
    const form = document.getElementById(formId);
    if (form) { form.reset(); }
}

function formatarData(isoString) {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function formatarNumero(valor) {
    return Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

/* ── Carrega selects de categorias dinamicamente ─────────────── */
async function carregarCategorias(selectId, valorSelecionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    try {
        const cats = await api.get('/categorias/');
        select.innerHTML = '<option value="">Selecione uma categoria</option>' +
            cats.map(c => `<option value="${c.idCategoria}"
                ${c.idCategoria == valorSelecionado ? 'selected' : ''}>${c.nome}</option>`).join('');
    } catch {
        select.innerHTML = '<option value="">Erro ao carregar categorias</option>';
    }
}

/* ── Carrega selects de produtos dinamicamente ───────────────── */
async function carregarProdutos(selectId, valorSelecionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    try {
        const prods = await api.get('/produtos/?apenas_ativos=true');
        // Ordena por descrição respeitando acentos do pt-BR (Á antes de B).
        prods.sort((a, b) => a.descricao.localeCompare(b.descricao, 'pt-BR', { sensitivity: 'base' }));
        select.innerHTML = '<option value="">Selecione um produto</option>' +
            prods.map(p => `<option value="${p.idProduto}"
                ${p.idProduto == valorSelecionado ? 'selected' : ''}>${p.descricao}</option>`).join('');
    } catch {
        select.innerHTML = '<option value="">Erro ao carregar produtos</option>';
    }
}
