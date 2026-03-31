PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS nf_sequences (
    serie         TEXT PRIMARY KEY,
    ultimo_numero INTEGER NOT NULL DEFAULT 0,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notas_fiscais (
    id                   TEXT PRIMARY KEY,
    numero               INTEGER NOT NULL,
    serie                TEXT NOT NULL DEFAULT '1',
    chave_acesso         TEXT UNIQUE NOT NULL,
    status               TEXT NOT NULL DEFAULT 'emitida'
                         CHECK(status IN ('emitida', 'cancelada')),
    data_emissao         TEXT NOT NULL,
    hora_emissao         TEXT NOT NULL,
    natureza_op          TEXT NOT NULL DEFAULT 'VENDA DE MERCADORIA',

    emit_razao           TEXT NOT NULL,
    emit_cnpj            TEXT NOT NULL,
    emit_ie              TEXT,
    emit_im              TEXT,
    emit_endereco        TEXT,
    emit_bairro          TEXT,
    emit_municipio       TEXT,
    emit_uf              TEXT,
    emit_cep             TEXT,
    emit_fone            TEXT,

    dest_nome            TEXT NOT NULL,
    dest_cpf_cnpj        TEXT,
    dest_ie              TEXT,
    dest_endereco        TEXT,
    dest_bairro          TEXT,
    dest_municipio       TEXT,
    dest_uf              TEXT,
    dest_cep             TEXT,
    dest_fone            TEXT,

    total_produtos       REAL NOT NULL DEFAULT 0,
    total_icms           REAL NOT NULL DEFAULT 0,
    total_ipi            REAL NOT NULL DEFAULT 0,
    total_frete          REAL NOT NULL DEFAULT 0,
    total_seguro         REAL NOT NULL DEFAULT 0,
    total_desconto       REAL NOT NULL DEFAULT 0,
    total_nota           REAL NOT NULL DEFAULT 0,

    transp_frete_conta   TEXT DEFAULT '0',
    info_complementar    TEXT,
    motivo_cancelamento  TEXT,

    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL,

    UNIQUE(numero, serie)
);

CREATE TABLE IF NOT EXISTS nf_itens (
    id              TEXT PRIMARY KEY,
    nota_id         TEXT NOT NULL REFERENCES notas_fiscais(id) ON DELETE CASCADE,
    seq             INTEGER NOT NULL,
    codigo_produto  TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    ncm             TEXT NOT NULL DEFAULT '',
    cst             TEXT NOT NULL DEFAULT '000',
    cfop            TEXT NOT NULL DEFAULT '5102',
    unidade         TEXT NOT NULL DEFAULT 'UN',
    quantidade      REAL NOT NULL CHECK(quantidade > 0),
    valor_unitario  REAL NOT NULL CHECK(valor_unitario >= 0),
    valor_total     REAL NOT NULL,
    bc_icms         REAL NOT NULL DEFAULT 0,
    aliquota_icms   REAL NOT NULL DEFAULT 0,
    valor_icms      REAL NOT NULL DEFAULT 0,
    aliquota_ipi    REAL NOT NULL DEFAULT 0,
    valor_ipi       REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS produtos (
    codigo          TEXT PRIMARY KEY,
    nome            TEXT NOT NULL,
    descricao_danfe TEXT NOT NULL,
    ncm             TEXT NOT NULL DEFAULT '',
    unidade         TEXT NOT NULL DEFAULT 'UN',
    valor_unitario  REAL NOT NULL CHECK(valor_unitario >= 0),
    aliquota_icms   REAL NOT NULL DEFAULT 0,
    cfop            TEXT NOT NULL DEFAULT '5102',
    ativo           INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN (0, 1)),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         TEXT PRIMARY KEY,
    tabela     TEXT NOT NULL,
    operacao   TEXT NOT NULL,
    ref_id     TEXT,
    dados      TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notas_status ON notas_fiscais(status);
CREATE INDEX IF NOT EXISTS idx_notas_numero ON notas_fiscais(numero DESC);
CREATE INDEX IF NOT EXISTS idx_notas_dest_nome ON notas_fiscais(dest_nome);
CREATE INDEX IF NOT EXISTS idx_itens_nota_id ON nf_itens(nota_id);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo_codigo ON produtos(ativo, codigo);
