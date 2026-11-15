# Backup e atualização

Tudo que importa mora num arquivo só: o banco SQLite, com leads, fluxos, etiquetas, campos, histórico e credenciais. Mais uma chave no `.env`.

## O que guardar

1. **O banco.** Baixe pelo painel ou pela linha de comando (abaixo).
2. **A `CEQ_ENCRYPTION_KEY` original.** Novas credenciais são cifradas com essa chave; guarde uma cópia segura separada do banco. Sem a chave original os valores cifrados não podem ser lidos.

Guarde os dois fora do servidor, em lugares diferentes. O backup tem o acesso da sua conta do Instagram dentro: trate como senha.

## Baixar o backup

**Pelo painel:** **Configurações → Backup → Baixar backup do banco**. Sai um arquivo `comentaeuquero-backup.db`.

A cópia é feita com o app rodando, sem parar nada, e não leva as sessões de login do painel.

## Restaurar

Na pasta do `docker-compose.yml` (no Docker manual, `/opt/ceq`), com o arquivo `comentaeuquero-backup.db` nela:

```bash
docker compose stop ceq
docker compose run --rm --no-deps -v "$PWD":/b --entrypoint sh ceq -c \
  "cp /b/comentaeuquero-backup.db /data/comentaeuquero.db && rm -f /data/comentaeuquero.db-wal /data/comentaeuquero.db-shm"
docker compose up -d
```

Confira que o `.env` tem a mesma `CEQ_ENCRYPTION_KEY` de quando o backup foi feito.

> [!TIP]
> **Faça um teste**
>
> Restaure uma vez num computador, antes de precisar. Backup que nunca foi testado não é backup.

## Atualizar

**Docker manual:**

```bash
cd /opt/ceq
sudo docker compose pull
sudo docker compose up -d
```

Com a tag `:estavel`, isso pega a última versão final. Com uma versão fixa (`:1.7.3`), troque o número no `docker-compose.yml` antes do `pull`.

O banco é atualizado sozinho quando a versão nova sobe. As mudanças de banco só acrescentam; não apagam dado.

### Cifrar credenciais de uma instalação antiga

Depois de criar um backup e testar sua restauração em ambiente isolado, confirme que a chave original está disponível à aplicação e execute no ambiente da instância:

```bash
python -m app.migrar_credenciais --backup-testado
```

A migração valida as credenciais já cifradas, recusa chave incompatível e converte os valores legados em uma transação. Se não existir valor cifrado, ela não consegue provar que a chave escolhida é a original. Ela pode ser repetida. Backups anteriores, páginas livres e arquivos WAL podem conter valores antigos em texto legível: mantenha-os protegidos e aplique uma política segura de retenção. Não gere uma chave nova para substituir a original de dados já cifrados.

## Conferir a versão

Logado no painel, abra `https://SEU-ENDERECO/health`. O campo `versao` mostra a versão rodando.

## Levar embora

O sistema é seu. Para mudar de servidor: baixe o backup, copie o `.env`, suba a instalação nova, restaure e atualize o `BASE_URL` e as URLs na Meta, se o endereço mudou ([domínio próprio](./dominio-proprio.md) explica quais).
