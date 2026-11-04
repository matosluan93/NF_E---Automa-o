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

O acesso à API é local por padrão. Para acesso remoto, configure a variável de ambiente
NFE_ACCESS_PASSWORD com uma senha aleatória de pelo menos 16 caracteres, use o usuário
nfe e publique o servidor por um proxy HTTPS. Configure NFE_PUBLIC_ORIGIN com a origem
pública HTTPS quando o proxy terminar o TLS. O endpoint /api/health continua público.
