-- =============================================================
-- Sistema de Controle de Materiais de Consumo — ASAC
-- Script de criação do banco de dados SQLite
-- =============================================================

PRAGMA foreign_keys = ON;   -- ativa checagem de FKs no SQLite
PRAGMA journal_mode = WAL;  -- gravações mais seguras em acesso concorrente

-- =============================================================
-- TABELA: categoria
-- Cobre: RF-01f (cadastro de categorias)
-- =============================================================
CREATE TABLE IF NOT EXISTS categoria (
    idCategoria  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT    NOT NULL UNIQUE,   -- ex.: LIMPEZA, COZINHA, ESCRITÓRIO
    descricao    TEXT
);

-- =============================================================
-- TABELA: produto
-- Cobre: RF-01a (cadastrar), RF-01b (alterar), RF-01c (desativar),
--        RF-01d (consultar), RF-01e (estoque mínimo)
-- =============================================================
CREATE TABLE IF NOT EXISTS produto (
    idProduto     INTEGER PRIMARY KEY AUTOINCREMENT,
    codBarras     TEXT    UNIQUE,                           -- pode ser nulo se não tiver código
    descricao     TEXT    NOT NULL,
    marca         TEXT,
    idCategoria   INTEGER NOT NULL
                  REFERENCES categoria(idCategoria),
    estoqueMinimo NUMERIC NOT NULL DEFAULT 0
                  CHECK (estoqueMinimo >= 0),
    -- saldoAtual é snapshot mantido por trigger após cada movimentação.
    -- Alternativa: omitir e calcular via SELECT SUM. Optamos por snapshot
    -- para leitura mais rápida em hardware antigo (RF-03 — 10 segundos).
    saldoAtual    NUMERIC NOT NULL DEFAULT 0,
    produtoAtivo  INTEGER NOT NULL DEFAULT 1
                  CHECK (produtoAtivo IN (0, 1)),           -- soft delete (RF-01c)
    dataCadastro  TEXT    NOT NULL DEFAULT (date('now'))
);

-- =============================================================
-- TABELA: usuario
-- Cobre: RF-04a (cadastrar), RF-04b (alterar perfil),
--        RF-04c (desativar — RN-04: nunca excluir)
-- =============================================================
CREATE TABLE IF NOT EXISTS usuario (
    idUsuario    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT    NOT NULL,
    login        TEXT    NOT NULL UNIQUE,
    senhaHash    TEXT    NOT NULL,                          -- bcrypt/argon2, nunca plain text
    perfil       TEXT    NOT NULL
                 CHECK (perfil IN ('ADMINISTRADOR', 'OPERADOR', 'CONSULTA')),
    usuarioAtivo INTEGER NOT NULL DEFAULT 1
                 CHECK (usuarioAtivo IN (0, 1)),            -- RN-04: desativar, nunca excluir
    dataCadastro TEXT    NOT NULL DEFAULT (date('now'))
);

-- =============================================================
-- TABELA: movimentacao
-- Cobre: RF-02a (registrar entrada), RF-02b (registrar saída),
--        RF-03 (base para relatórios e consultas de histórico)
-- =============================================================
CREATE TABLE IF NOT EXISTS movimentacao (
    idMovimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
    tipoMov        TEXT    NOT NULL
                   CHECK (tipoMov IN ('ENTRADA', 'SAIDA', 'AJUSTE', 'DESCARTE')),
    dataMov        TEXT    NOT NULL DEFAULT (datetime('now')),
    quantMov       NUMERIC NOT NULL CHECK (quantMov > 0),
    idProduto      INTEGER NOT NULL
                   REFERENCES produto(idProduto),
    idUsuario      INTEGER NOT NULL
                   REFERENCES usuario(idUsuario),
    observacao     TEXT                                     -- obrigatório para AJUSTE/DESCARTE via app
);

-- =============================================================
-- TRIGGER: atualiza saldoAtual após cada movimentação
-- ENTRADA e AJUSTE somam; SAIDA e DESCARTE subtraem.
-- =============================================================
CREATE TRIGGER IF NOT EXISTS trg_atualiza_saldo
AFTER INSERT ON movimentacao
BEGIN
    UPDATE produto
    SET saldoAtual = saldoAtual +
        CASE NEW.tipoMov
            WHEN 'ENTRADA'  THEN  NEW.quantMov
            WHEN 'AJUSTE'   THEN  NEW.quantMov
            WHEN 'SAIDA'    THEN -NEW.quantMov
            WHEN 'DESCARTE' THEN -NEW.quantMov
        END
    WHERE idProduto = NEW.idProduto;
END;

-- =============================================================
-- ÍNDICES — aceleram as consultas mais frequentes (RF-03)
-- =============================================================
CREATE INDEX IF NOT EXISTS idx_produto_categoria  ON produto(idCategoria);
CREATE INDEX IF NOT EXISTS idx_produto_codbarras  ON produto(codBarras);
CREATE INDEX IF NOT EXISTS idx_mov_produto        ON movimentacao(idProduto);
CREATE INDEX IF NOT EXISTS idx_mov_usuario        ON movimentacao(idUsuario);
CREATE INDEX IF NOT EXISTS idx_mov_data           ON movimentacao(dataMov);

-- =============================================================
-- DADOS INICIAIS (seed)
-- =============================================================

-- Categorias padrão
INSERT OR IGNORE INTO categoria (nome, descricao) VALUES
    ('LIMPEZA',    'Produtos de higiene e limpeza geral'),
    ('COZINHA',    'Itens de copa e cozinha'),
    ('ESCRITÓRIO', 'Materiais de expediente e papelaria');

-- Usuário administrador padrão (senha deve ser trocada no primeiro acesso)
-- Hash de exemplo — substituir pelo hash real gerado via bcrypt/argon2
INSERT OR IGNORE INTO usuario (nome, login, senhaHash, perfil) VALUES
    ('Administrador', 'admin', 'TROCAR_ANTES_DE_USAR', 'ADMINISTRADOR');
