# Arquitetura

## Backend
- Flask com application factory
- Camadas separadas: API, services, repositories, validators e DB
- SQLite com WAL e foreign keys
- Seed inicial do catálogo em `data/catalogo.json`

## Frontend
- Interface estática servida pelo Flask
- Configuração central em `frontend/config.js`
- `index.html` + CSS + JS separados
- Consome a API REST em `/api`
