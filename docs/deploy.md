# Deploy

## Execução local
```bash
bash scripts/start.sh
```

## Produção
```bash
gunicorn --chdir backend wsgi:app
```

Use a variável `DB_PATH` apontando para um disco persistente.
