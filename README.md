# Sistema NF-e Stefanini — versão refatorada

Projeto reorganizado para manutenção de longo prazo, mantendo o mesmo contrato principal de API e a interface DANFE.

## Estrutura

```text
nfe_system_sustentavel/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── validators/
│   │   └── utils/
│   ├── tests/
│   └── wsgi.py
├── frontend/
│   ├── index.html
│   ├── config.js
│   └── assets/
├── data/
│   └── catalogo.json
├── db/
├── scripts/
├── docs/
├── requirements.txt
└── .env.example
```

## Como rodar

### Linux/macOS
```bash
bash scripts/start.sh
```

### Windows
```bat
scripts\start.bat
```

Depois abra `http://localhost:5000`.

## Melhorias implementadas
- backend modular com camadas
- seed do catálogo separado do código de aplicação
- configuração por variáveis de ambiente
- tratamento de erros centralizado
- `requirements.txt` e scripts de inicialização
- frontend separado em HTML/CSS/JS
- caminho do banco configurável via `DB_PATH`
