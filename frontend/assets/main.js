'use strict';

const CONFIG = Object.freeze(window.NFE_CONFIG || {});
const EMITENTE = Object.freeze(CONFIG.emitente || {});

class ApiError extends Error {
  constructor(message, status = 500) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

const Utils = {
  esc: (str) => String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;'),
  fmtNum: (n) => Number(n || 0).toFixed(2).replace('.', ','),
  fmtBRL: (n) => `R$ ${Utils.fmtNum(n)}`,
  fmtDate: (d) => {
    if (!d) return '—';
    const [y, m, dd] = String(d).split('-');
    return dd && m && y ? `${dd}/${m}/${y}` : d;
  },
  pad: (n, len = 6) => String(n ?? '').padStart(len, '0'),
  today: () => new Date().toISOString().split('T')[0],
  nowTime: () => new Date().toTimeString().slice(0, 5),
  r2: (n) => Math.round((Number(n || 0) + Number.EPSILON) * 100) / 100,
  debounce(fn, ms = 250) {
    let t = null;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }
};

const Toast = {
  show(message, type = 'info', duration = CONFIG.TOAST_DURATION_MS || 4000) {
    const box = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = Utils.esc(message);
    box.appendChild(el);
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 220);
    }, duration);
  },
  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error'); },
  info(msg) { this.show(msg, 'info'); }
};

const Loading = {
  count: 0,
  show() {
    this.count++;
    document.getElementById('loading').classList.add('show');
  },
  hide() {
    this.count = Math.max(0, this.count - 1);
    if (!this.count) document.getElementById('loading').classList.remove('show');
  }
};

const Api = {
  async request(path, options = {}) {
    const response = await fetch(`${CONFIG.API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const msg = typeof data === 'string'
        ? data
        : (data?.erro || data?.mensagem || 'Erro na requisição');
      throw new ApiError(msg, response.status);
    }
    return data;
  },
  get(path) { return this.request(path); },
  post(path, body) {
    return this.request(path, { method: 'POST', body: JSON.stringify(body) });
  }
};

const Health = {
  async check() {
    const dot = document.getElementById('api-dot');
    const status = document.getElementById('api-status');
    try {
      await Api.get('/dashboard');
      dot.className = 'api-dot online';
      status.textContent = 'API conectada';
      return true;
    } catch {
      dot.className = 'api-dot offline';
      status.textContent = 'Servidor offline';
      return false;
    }
  },
  start() {
    this.check();
    setInterval(() => this.check(), CONFIG.HEALTH_INTERVAL_MS || 30000);
  }
};

const Store = {
  products: [],
  items: [],
  currentNotaId: null,
};

const Views = {
  show(name) {
    document.querySelectorAll('.view').forEach(el => el.classList.remove('view-active'));
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    document.getElementById(`view-${name}`)?.classList.add('view-active');
    document.querySelector(`.tab[data-view="${name}"]`)?.classList.add('active');

    if (name === 'notas') Notas.load();
    if (name === 'dashboard') Dashboard.load();
  }
};

const Products = {
  async load() {
    Store.products = await Api.get('/produtos');
  },

  bindSearch() {
    const input = document.getElementById('prod-search');
    const dropdown = document.getElementById('prod-dropdown');

    const render = () => {
      const q = input.value.trim().toLowerCase();
      if (!q) {
        dropdown.classList.remove('open');
        dropdown.innerHTML = '';
        return;
      }

      const result = Store.products.filter(p =>
        String(p.codigo).toLowerCase().includes(q) ||
        String(p.nome).toLowerCase().includes(q) ||
        String(p.descricao_danfe || '').toLowerCase().includes(q)
      ).slice(0, 15);

      if (!result.length) {
        dropdown.innerHTML = '<div class="dd-empty">Nenhum produto encontrado</div>';
        dropdown.classList.add('open');
        return;
      }

      dropdown.innerHTML = result.map(p => `
        <div class="dd-item" data-code="${Utils.esc(p.codigo)}">
          <div class="dd-code">${Utils.esc(p.codigo)}</div>
          <div class="dd-name">${Utils.esc(p.descricao_danfe || p.nome)}</div>
          <div class="dd-price">${Utils.fmtBRL(p.valor_unitario)}</div>
        </div>
      `).join('');
      dropdown.classList.add('open');
    };

    input.addEventListener('input', Utils.debounce(render, CONFIG.SEARCH_DEBOUNCE_MS || 250));

    dropdown.addEventListener('click', (event) => {
      const item = event.target.closest('.dd-item');
      if (!item) return;
      const code = item.dataset.code;
      const product = Store.products.find(p => String(p.codigo) === String(code));
      if (product) Items.add(product);
      input.value = '';
      dropdown.classList.remove('open');
      dropdown.innerHTML = '';
      input.focus();
    });

    document.addEventListener('click', (event) => {
      if (!event.target.closest('.product-search')) dropdown.classList.remove('open');
    });
  }
};

const Items = {
  add(product) {
    const existing = Store.items.find(i => i.codigo === product.codigo);
    if (existing) {
      existing.qty += 1;
    } else {
      Store.items.push({ ...product, qty: 1 });
    }
    this.render();
  },

  remove(code) {
    Store.items = Store.items.filter(item => item.codigo !== code);
    this.render();
  },

  changeQty(code, value) {
    const item = Store.items.find(i => i.codigo === code);
    if (!item) return;
    item.qty = Math.max(1, parseInt(value, 10) || 1);
    this.render();
  },

  clear() {
    Store.items = [];
    this.render();
  },

  render() {
    const tbody = document.getElementById('items-body');
    if (!Store.items.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="6">Nenhum produto adicionado</td></tr>';
      document.getElementById('tot-itens').textContent = '0';
      document.getElementById('tot-icms').textContent = 'R$ 0,00';
      document.getElementById('tot-total').textContent = 'R$ 0,00';
      return;
    }

    tbody.innerHTML = Store.items.map(item => {
      const total = Utils.r2(item.qty * Number(item.valor_unitario || 0));
      return `
        <tr>
          <td class="mono" style="font-size:11px;color:#7fa4ff">${Utils.esc(item.codigo)}</td>
          <td>${Utils.esc(item.descricao_danfe || item.nome)}</td>
          <td><input type="number" min="1" value="${item.qty}" data-qtd="${Utils.esc(item.codigo)}" /></td>
          <td class="mono">${Utils.fmtBRL(item.valor_unitario)}</td>
          <td class="mono">${Utils.fmtBRL(total)}</td>
          <td><button class="icon-btn" data-remove="${Utils.esc(item.codigo)}" title="Remover item">×</button></td>
        </tr>`;
    }).join('');

    const totalProdutos = Utils.r2(Store.items.reduce((sum, item) => sum + (item.qty * Number(item.valor_unitario || 0)), 0));
    const totalIcms = Utils.r2(Store.items.reduce((sum, item) =>
      sum + (item.qty * Number(item.valor_unitario || 0) * Number(item.aliquota_icms || 0)), 0));

    document.getElementById('tot-itens').textContent = String(Store.items.length);
    document.getElementById('tot-icms').textContent = Utils.fmtBRL(totalIcms);
    document.getElementById('tot-total').textContent = Utils.fmtBRL(totalProdutos);

    tbody.querySelectorAll('[data-remove]').forEach(btn => {
      btn.addEventListener('click', () => this.remove(btn.dataset.remove));
    });

    tbody.querySelectorAll('[data-qtd]').forEach(input => {
      input.addEventListener('change', () => this.changeQty(input.dataset.qtd, input.value));
    });
  }
};

const Form = {
  init() {
    document.getElementById('f-data').value = Utils.today();
    document.getElementById('f-hora').value = Utils.nowTime();
    document.getElementById('f-info').value = CONFIG.infoComplementarDefault || '';
    document.getElementById('f-serie').addEventListener('change', () => this.fetchNextNumber());

    document.getElementById('btn-preview').addEventListener('click', () => this.preview());
    document.getElementById('btn-refresh-preview').addEventListener('click', () => this.preview());
    document.getElementById('btn-emitir').addEventListener('click', () => this.emitir());
  },

  async fetchNextNumber() {
    try {
      const serie = document.getElementById('f-serie').value;
      const data = await Api.get(`/numeracao/proximo/${encodeURIComponent(serie)}`);
      document.getElementById('f-numero').value = Utils.pad(data.proximo, 6);
    } catch {
      document.getElementById('f-numero').value = '------';
    }
  },

  getPayload() {
    return {
      serie: document.getElementById('f-serie').value,
      data_emissao: document.getElementById('f-data').value,
      hora_emissao: document.getElementById('f-hora').value,
      natureza_op: document.getElementById('f-natureza').value.trim(),
      dest_nome: document.getElementById('f-dest-nome').value.trim(),
      dest_cpf_cnpj: document.getElementById('f-dest-cpf').value.trim(),
      dest_ie: document.getElementById('f-dest-ie').value.trim(),
      dest_endereco: document.getElementById('f-dest-end').value.trim(),
      dest_bairro: document.getElementById('f-dest-bairro').value.trim(),
      dest_municipio: document.getElementById('f-dest-mun').value.trim(),
      dest_uf: document.getElementById('f-dest-uf').value,
      dest_cep: document.getElementById('f-dest-cep').value.trim(),
      dest_fone: document.getElementById('f-dest-fone').value.trim(),
      info_complementar: document.getElementById('f-info').value.trim(),
      itens: Store.items.map(item => ({
        codigo_produto: item.codigo,
        descricao: item.descricao_danfe || item.nome,
        ncm: item.ncm || '',
        cst: '000',
        cfop: item.cfop || '5102',
        unidade: item.unidade || 'UN',
        quantidade: item.qty,
        valor_unitario: Number(item.valor_unitario || 0),
        aliquota_icms: Number(item.aliquota_icms || 0),
        aliquota_ipi: 0,
      }))
    };
  },

  validate() {
    const nome = document.getElementById('f-dest-nome');
    nome.classList.remove('error');

    if (!nome.value.trim()) {
      nome.classList.add('error');
      nome.focus();
      Toast.error('Informe o nome do destinatário');
      return false;
    }
    if (!Store.items.length) {
      Toast.error('Adicione ao menos um item à nota');
      document.getElementById('prod-search').focus();
      return false;
    }
    return true;
  },

  preview() {
    document.getElementById('danfe-output').innerHTML = Danfe.build({});
  },

  async emitir() {
    if (!this.validate()) return;
    const btn = document.getElementById('btn-emitir');
    btn.disabled = true;
    Loading.show();

    try {
      const nota = await Api.post('/notas', this.getPayload());
      document.getElementById('danfe-output').innerHTML = Danfe.build(nota);
      Toast.success(`NF nº ${Utils.pad(nota.numero, 6)} emitida com sucesso`);
      this.reset();
      await this.fetchNextNumber();
      Notas.load();
      Dashboard.load();
    } catch (err) {
      Toast.error(err instanceof ApiError ? err.message : 'Erro ao emitir nota');
    } finally {
      btn.disabled = false;
      Loading.hide();
    }
  },

  reset() {
    ['f-dest-nome','f-dest-cpf','f-dest-ie','f-dest-end','f-dest-bairro','f-dest-mun','f-dest-cep','f-dest-fone']
      .forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
    document.getElementById('f-info').value = CONFIG.infoComplementarDefault || '';
    Items.clear();
  }
};

function gerarChaveAcesso(cnpj, serie, numero, dataEmissao) {
  const cnpjD = String(cnpj || '').replace(/\D/g, '').padStart(14, '0');
  const clean = String(dataEmissao || '').replace(/-/g, '');
  const aamm = clean.length >= 6 ? clean.slice(2, 6) : '2509';
  const mod = '55';
  const s = String(serie || 1).padStart(3, '0');
  const n = String(numero || 0).padStart(9, '0');
  const tpEmis = '1';
  const cNF = String(Math.floor(Math.random() * 99999999)).padStart(8, '0');
  const raw = `${EMITENTE.uf_codigo || '35'}${aamm}${cnpjD}${mod}${s}${n}${tpEmis}${cNF}`;
  const pesos = [2,3,4,5,6,7,8,9];
  let soma = 0;
  for (let i = raw.length - 1, p = 0; i >= 0; i--, p = (p + 1) % 8) {
    soma += Number(raw[i]) * pesos[p];
  }
  const dv = 11 - (soma % 11);
  const cDV = dv >= 2 ? dv : 0;
  return `${raw}${cDV}`.match(/.{1,4}/g).join(' ');
}

const Danfe = {
  build(nota) {
    const numero = nota.numero ?? document.getElementById('f-numero').value;
    const serie = nota.serie ?? document.getElementById('f-serie').value;
    const data = nota.data_emissao ?? document.getElementById('f-data').value;
    const hora = nota.hora_emissao ?? document.getElementById('f-hora').value;
    const natureza = nota.natureza_op ?? document.getElementById('f-natureza').value;
    const info = nota.info_complementar ?? document.getElementById('f-info').value;

    const destNome = nota.dest_nome ?? document.getElementById('f-dest-nome').value;
    const destCpf = nota.dest_cpf_cnpj ?? document.getElementById('f-dest-cpf').value;
    const destIe = nota.dest_ie ?? document.getElementById('f-dest-ie').value;
    const destEnd = nota.dest_endereco ?? document.getElementById('f-dest-end').value;
    const destBairro = nota.dest_bairro ?? document.getElementById('f-dest-bairro').value;
    const destMun = nota.dest_municipio ?? document.getElementById('f-dest-mun').value;
    const destUf = nota.dest_uf ?? document.getElementById('f-dest-uf').value;
    const destCep = nota.dest_cep ?? document.getElementById('f-dest-cep').value;
    const destFone = nota.dest_fone ?? document.getElementById('f-dest-fone').value;

    const itens = Array.isArray(nota.itens)
      ? nota.itens
      : Store.items.map(item => {
          const total = Utils.r2(item.qty * Number(item.valor_unitario || 0));
          const valorIcms = Utils.r2(total * Number(item.aliquota_icms || 0));
          return {
            codigo_produto: item.codigo,
            descricao: item.descricao_danfe || item.nome,
            ncm: item.ncm || '',
            cst: '000',
            cfop: String(item.cfop || '5102').replace(/\./g, ''),
            unidade: item.unidade || 'UN',
            quantidade: item.qty,
            valor_unitario: Number(item.valor_unitario || 0),
            valor_total: total,
            bc_icms: total,
            aliquota_icms: Number(item.aliquota_icms || 0),
            valor_icms: valorIcms,
            aliquota_ipi: 0,
            valor_ipi: 0,
          };
        });

    const totalProdutos = nota.total_produtos ?? Utils.r2(itens.reduce((sum, item) => sum + Number(item.valor_total || 0), 0));
    const totalIcms = nota.total_icms ?? Utils.r2(itens.reduce((sum, item) => sum + Number(item.valor_icms || 0), 0));
    const totalNota = nota.total_nota ?? totalProdutos;
    const chave = nota.chave_acesso || gerarChaveAcesso(EMITENTE.cnpj, serie, numero, data);
    const protocolo = nota.id ? String(nota.id).split('-')[0].toUpperCase() : '(aguardando emissão)';
    const cancelBanner = nota.status === 'cancelada'
      ? `<div class="d-cancel">✕ NOTA FISCAL CANCELADA ✕</div>`
      : '';

    const rows = itens.length
      ? itens.map(item => {
          const aliquota = `${(Number(item.aliquota_icms || 0) * 100).toFixed(2).replace('.', ',')}`;
          return `
            <tr>
              <td>${Utils.esc(item.codigo_produto)}</td>
              <td>${Utils.esc(item.descricao)}</td>
              <td>${Utils.esc(item.ncm || '')}</td>
              <td>${Utils.esc(item.cst || '000')}</td>
              <td>${Utils.esc(String(item.cfop || '5102').replace(/\./g, ''))}</td>
              <td>${Utils.esc(item.unidade || 'UN')}</td>
              <td class="d-center">${Utils.esc(Number(item.quantidade || 0).toFixed(2).replace('.', ','))}</td>
              <td class="d-right">${Utils.fmtNum(item.valor_unitario)}</td>
              <td class="d-right">${Utils.fmtNum(item.valor_total)}</td>
              <td class="d-right">${Utils.fmtNum(item.bc_icms ?? item.valor_total)}</td>
              <td class="d-right">${Utils.fmtNum(item.valor_icms)}</td>
              <td class="d-right">${aliquota}</td>
              <td class="d-right">${Utils.fmtNum(item.valor_ipi || 0)}</td>
            </tr>`;
        }).join('')
      : '<tr><td colspan="13" class="d-center">Nenhum item adicionado</td></tr>';

    return `
      <div class="danfe">
        <div class="d-receipt">
          <div class="d-receipt-left">
            <div>RECEBEMOS DE ${Utils.esc(EMITENTE.razao)} OS PRODUTOS CONSTANTES NA NOTA FISCAL AO LADO</div>
            <div style="display:flex">
              <div style="flex:1;border-top:1px solid #000;padding-top:3px">DATA DE RECEBIMENTO</div>
              <div style="flex:2;border-top:1px solid #000;border-left:1px solid #000;padding:3px 4px 0">IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR</div>
            </div>
          </div>
          <div class="d-receipt-right">
            <strong>NF-e</strong>
            <div>Nº ${Utils.pad(numero, 6)}</div>
            <div>SÉRIE ${Utils.esc(serie)}</div>
          </div>
        </div>
        <div class="d-divider"></div>
        ${cancelBanner}
        <div class="d-body">
          <div class="d-line">
            <div class="d-cell d-header-left">
              <div class="d-logo-wrap">
                <img src="${Utils.esc(CONFIG.LOGO_PATH || './assets/img/logo-stefanini-4k.png')}" alt="Stefanini Group" class="d-logo" />
              </div>
              <div class="d-value small" style="margin-top:4px">
                ${Utils.esc(EMITENTE.razao)}<br>
                ${Utils.esc(EMITENTE.endereco)} - ${Utils.esc(EMITENTE.bairro)}<br>
                ${Utils.esc(EMITENTE.municipio)} - ${Utils.esc(EMITENTE.uf)}<br>
                ${Utils.esc(EMITENTE.fone)} - ${Utils.esc(EMITENTE.cep)}
              </div>
            </div>
            <div class="d-cell d-header-center">
              <div class="d-danfe-title">DANFE</div>
              <div>Documento Auxiliar da</div>
              <div>Nota Fiscal Eletrônica</div>
              <div style="margin-top:8px;font-size:10px;font-weight:bold">0 - ENTRADA &nbsp;&nbsp; 1 - SAÍDA</div>
              <div style="margin-top:8px;font-size:12px;font-weight:bold">Nº ${Utils.pad(numero, 6)}</div>
              <div style="font-size:11px;font-weight:bold">SÉRIE ${Utils.esc(serie)}</div>
            </div>
            <div class="d-cell d-header-right">
              <div class="d-label">Chave de acesso</div>
              <div class="d-barcode"></div>
              <div class="d-value small" style="text-align:center;margin-top:4px">${Utils.esc(chave)}</div>
              <div class="d-value small" style="text-align:center;margin-top:6px">
                Consulta de autenticidade no portal nacional da NF-e<br>
                www.nfe.fazenda.gov.br/portal ou no site da Sefaz Autorizadora
              </div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1.35">
              <span class="d-label">Natureza da operação</span>
              <div class="d-value">${Utils.esc(natureza || 'VENDA DE MERCADORIA')}</div>
            </div>
            <div class="d-cell" style="width:220px">
              <span class="d-label">Protocolo de autorização de uso</span>
              <div class="d-value">${Utils.esc(protocolo)}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1">
              <span class="d-label">Inscrição estadual</span>
              <div class="d-value">${Utils.esc(EMITENTE.ie || '')}</div>
            </div>
            <div class="d-cell" style="flex:1">
              <span class="d-label">Insc. estadual do subst. tributário</span>
              <div class="d-value">&nbsp;</div>
            </div>
            <div class="d-cell" style="width:210px">
              <span class="d-label">CNPJ</span>
              <div class="d-value">${Utils.esc(EMITENTE.cnpj || '')}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1">
              <span class="d-label">Destinatário / Remetente</span>
              <div class="d-value">${Utils.esc(destNome || '—')}</div>
            </div>
            <div class="d-cell" style="width:170px">
              <span class="d-label">CNPJ / CPF</span>
              <div class="d-value">${Utils.esc(destCpf || '')}</div>
            </div>
            <div class="d-cell" style="width:120px">
              <span class="d-label">Data da emissão</span>
              <div class="d-value">${Utils.esc(Utils.fmtDate(data))}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1.5">
              <span class="d-label">Endereço</span>
              <div class="d-value">${Utils.esc(destEnd || '')}</div>
            </div>
            <div class="d-cell" style="width:170px">
              <span class="d-label">Bairro / Distrito</span>
              <div class="d-value">${Utils.esc(destBairro || '')}</div>
            </div>
            <div class="d-cell" style="width:90px">
              <span class="d-label">CEP</span>
              <div class="d-value">${Utils.esc(destCep || '')}</div>
            </div>
            <div class="d-cell" style="width:120px">
              <span class="d-label">Data da entrada / saída</span>
              <div class="d-value">${Utils.esc(Utils.fmtDate(data))}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1.2">
              <span class="d-label">Município</span>
              <div class="d-value">${Utils.esc(destMun || '')}</div>
            </div>
            <div class="d-cell" style="width:60px">
              <span class="d-label">UF</span>
              <div class="d-value">${Utils.esc(destUf || '')}</div>
            </div>
            <div class="d-cell" style="width:150px">
              <span class="d-label">Fone / Fax</span>
              <div class="d-value">${Utils.esc(destFone || '')}</div>
            </div>
            <div class="d-cell" style="width:140px">
              <span class="d-label">Inscrição estadual</span>
              <div class="d-value">${Utils.esc(destIe || '')}</div>
            </div>
            <div class="d-cell" style="width:110px">
              <span class="d-label">Hora da entrada / saída</span>
              <div class="d-value">${Utils.esc(hora || '')}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="width:130px">
              <span class="d-label">Base de cálculo do ICMS</span>
              <div class="d-value">${Utils.fmtNum(totalProdutos)}</div>
            </div>
            <div class="d-cell" style="width:120px">
              <span class="d-label">Valor do ICMS</span>
              <div class="d-value">${Utils.fmtNum(totalIcms)}</div>
            </div>
            <div class="d-cell" style="width:160px">
              <span class="d-label">Base de cálculo do ICMS ST</span>
              <div class="d-value">0,00</div>
            </div>
            <div class="d-cell" style="width:140px">
              <span class="d-label">Valor do ICMS ST</span>
              <div class="d-value">0,00</div>
            </div>
            <div class="d-cell" style="width:110px">
              <span class="d-label">Valor total dos produtos</span>
              <div class="d-value">${Utils.fmtNum(totalProdutos)}</div>
            </div>
            <div class="d-cell" style="flex:1">
              <span class="d-label">Valor total da nota</span>
              <div class="d-value">${Utils.fmtNum(totalNota)}</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1">
              <span class="d-label">Transportador / Volumes transportados</span>
              <div class="d-value">&nbsp;</div>
            </div>
            <div class="d-cell" style="width:150px">
              <span class="d-label">Frete por conta</span>
              <div class="d-value small">0 - Frete por conta do Remetente (CIF)</div>
            </div>
            <div class="d-cell" style="width:130px">
              <span class="d-label">Placa do veículo</span>
              <div class="d-value">&nbsp;</div>
            </div>
            <div class="d-cell" style="width:60px">
              <span class="d-label">UF</span>
              <div class="d-value">&nbsp;</div>
            </div>
            <div class="d-cell" style="width:150px">
              <span class="d-label">CNPJ / CPF</span>
              <div class="d-value">&nbsp;</div>
            </div>
          </div>

          <table class="d-table">
            <thead>
              <tr>
                <th>Cód. prod.</th>
                <th>Descrição do produto / serviço</th>
                <th>NCM / SH</th>
                <th>CST</th>
                <th>CFOP</th>
                <th>UNID</th>
                <th>Quantidade</th>
                <th>V. Unitário</th>
                <th>V. Total</th>
                <th>BC ICMS</th>
                <th>V. ICMS</th>
                <th>ALQ. ICMS</th>
                <th>V. IPI</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>

          <div class="d-footer-note">
            Trib aprox R$: ${Utils.fmtNum(totalIcms)} Federal e ${Utils.fmtNum(totalIcms)} Estadual e 0,00 Municipal.<br>
            Fonte: IBPT. ${Utils.esc(info || '')}
          </div>

          <div class="d-issqn">
            <div class="d-cell" style="width:140px">
              <span class="d-label">Inscrição municipal</span>
              <div class="d-value">${Utils.esc(EMITENTE.im || '')}</div>
            </div>
            <div class="d-cell" style="width:180px">
              <span class="d-label">Valor total dos serviços</span>
              <div class="d-value">0,00</div>
            </div>
            <div class="d-cell" style="width:180px">
              <span class="d-label">Base de cálculo do ISSQN</span>
              <div class="d-value">0,00</div>
            </div>
            <div class="d-cell" style="flex:1">
              <span class="d-label">Valor do ISSQN</span>
              <div class="d-value">0,00</div>
            </div>
          </div>

          <div class="d-line">
            <div class="d-cell" style="flex:1.8;min-height:92px">
              <span class="d-label">Informações complementares</span>
              <div class="d-value small">${Utils.esc(info || '').replace(/\n/g, '<br>')}</div>
            </div>
            <div class="d-cell" style="flex:1">
              <span class="d-label">Reservado ao fisco</span>
              <div class="d-value">&nbsp;</div>
            </div>
          </div>
        </div>
      </div>`;
  }
};

const Modal = {
  open(id) {
    Loading.show();
    Api.get(`/notas/${id}`)
      .then(nota => {
        Store.currentNotaId = nota.id;
        document.getElementById('modal-title').textContent = `NF nº ${Utils.pad(nota.numero, 6)} — ${nota.dest_nome}`;
        document.getElementById('modal-body').innerHTML = Danfe.build(nota);
        document.getElementById('btn-modal-cancel').style.display = nota.status === 'cancelada' ? 'none' : '';
        document.getElementById('modal-nota').classList.add('open');
      })
      .catch(err => Toast.error(err instanceof ApiError ? err.message : 'Erro ao carregar nota'))
      .finally(() => Loading.hide());
  },
  close() {
    document.getElementById('modal-nota').classList.remove('open');
    Store.currentNotaId = null;
  }
};

const Notas = {
  async load() {
    const tbody = document.getElementById('notas-body');
    tbody.innerHTML = '<tr class="empty-row"><td colspan="8">Carregando notas…</td></tr>';
    try {
      const q = document.getElementById('notas-search').value.trim();
      const data = await Api.get(`/notas?q=${encodeURIComponent(q)}&limit=100`);
      const list = data.notas || [];
      if (!list.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="8">Nenhuma nota encontrada</td></tr>';
        return;
      }
      tbody.innerHTML = list.map(n => `
        <tr>
          <td class="mono" style="color:#7fa4ff">${Utils.pad(n.numero, 6)}</td>
          <td class="mono">${Utils.esc(n.serie)}</td>
          <td>${Utils.fmtDate(n.data_emissao)}</td>
          <td title="${Utils.esc(n.dest_nome)}">${Utils.esc(n.dest_nome)}</td>
          <td class="mono">${Utils.fmtBRL(n.total_nota)}</td>
          <td class="mono">${Utils.fmtBRL(n.total_icms)}</td>
          <td><span class="badge ${n.status === 'emitida' ? 'badge-green' : 'badge-red'}">${Utils.esc(n.status)}</span></td>
          <td>
            <div class="td-actions">
              <button class="btn btn-secondary btn-sm" data-view="${Utils.esc(n.id)}">Ver</button>
              ${n.status === 'emitida' ? `<button class="btn btn-danger btn-sm" data-cancel="${Utils.esc(n.id)}">Cancelar</button>` : ''}
            </div>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', () => Modal.open(btn.dataset.view));
      });
      tbody.querySelectorAll('[data-cancel]').forEach(btn => {
        btn.addEventListener('click', () => this.cancelar(btn.dataset.cancel));
      });
    } catch (err) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="8">Erro ao carregar: ${Utils.esc(err.message || 'Falha')}</td></tr>`;
    }
  },

  async cancelar(id) {
    if (!confirm('Confirmar o cancelamento desta Nota Fiscal?')) return;
    Loading.show();
    try {
      await Api.post(`/notas/${id}/cancelar`, { motivo: 'Cancelamento solicitado pelo usuário' });
      Toast.success('Nota fiscal cancelada com sucesso');
      this.load();
      Dashboard.load();
      if (Store.currentNotaId === id) Modal.close();
    } catch (err) {
      Toast.error(err instanceof ApiError ? err.message : 'Erro ao cancelar');
    } finally {
      Loading.hide();
    }
  }
};

const Dashboard = {
  async load() {
    try {
      const data = await Api.get('/dashboard');
      document.getElementById('kpi-emitidas').textContent = data.total_emitidas ?? '0';
      document.getElementById('kpi-fat').textContent = Utils.fmtBRL(data.faturamento_total ?? 0);
      document.getElementById('kpi-cancel').textContent = data.total_canceladas ?? '0';
      const seq1 = (data.sequencias || []).find(s => String(s.serie) === '1');
      document.getElementById('kpi-serie').textContent = seq1
        ? `Último nº ${Utils.pad(seq1.ultimo_numero, 6)}`
        : 'Sem sequência';

      const tbody = document.getElementById('dash-body');
      const list = data.ultimas_notas || [];
      tbody.innerHTML = list.length ? list.map(n => `
        <tr>
          <td class="mono" style="color:#7fa4ff">${Utils.pad(n.numero, 6)}</td>
          <td>${Utils.fmtDate(n.data_emissao)}</td>
          <td>${Utils.esc(n.dest_nome)}</td>
          <td class="mono">${Utils.fmtBRL(n.total_nota)}</td>
          <td><span class="badge ${n.status === 'emitida' ? 'badge-green' : 'badge-red'}">${Utils.esc(n.status)}</span></td>
        </tr>
      `).join('') : '<tr class="empty-row"><td colspan="5">Nenhuma nota emitida</td></tr>';
    } catch {
      document.getElementById('kpi-emitidas').textContent = '—';
      document.getElementById('kpi-fat').textContent = '—';
      document.getElementById('kpi-cancel').textContent = '—';
      document.getElementById('kpi-serie').textContent = '—';
      document.getElementById('dash-body').innerHTML = '<tr class="empty-row"><td colspan="5">Não foi possível carregar o dashboard</td></tr>';
    }
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => Views.show(tab.dataset.view));
  });
  document.getElementById('btn-modal-close').addEventListener('click', () => Modal.close());
  document.getElementById('btn-modal-cancel').addEventListener('click', async () => {
    if (!Store.currentNotaId) return;
    await Notas.cancelar(Store.currentNotaId);
  });
  document.getElementById('modal-nota').addEventListener('click', (event) => {
    if (event.target.id === 'modal-nota') Modal.close();
  });
  document.getElementById('btn-reload-notas').addEventListener('click', () => Notas.load());
  document.getElementById('notas-search').addEventListener('input', Utils.debounce(() => Notas.load(), CONFIG.SEARCH_DEBOUNCE_MS || 250));

  Form.init();
  Health.start();
  Loading.show();
  try {
    await Products.load();
    Products.bindSearch();
    await Form.fetchNextNumber();
    Dashboard.load();
  } catch (err) {
    Toast.error(err instanceof ApiError ? err.message : 'Não foi possível iniciar a interface');
  } finally {
    Loading.hide();
  }
});