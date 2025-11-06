
# Publicando a CLI do OS Backup

## Opção 1: PyPI (Recomendado para Distribuição Pública)

### 1. Preparação

```bash
# Instalar ferramentas de build
pip install build twine

# Criar os pacotes de distribuição
python -m build
```

### 2. Testar Localmente

```bash
# Instalar localmente para testar
pip install -e .

# Testar a CLI
osbackup --help
osbackup hosts
osbackup status
```

### 3. Publicar no PyPI

```bash
# Criar conta em https://pypi.org/

# Upload para TestPyPI (teste primeiro)
twine upload --repository testpypi dist/*

# Upload para PyPI (produção)
twine upload dist/*
```

### 4. Instalação pelos Usuários

```bash
pip install os-backup-cli
osbackup --help
```

## Opção 2: GitHub Releases

### 1. Criar Release no GitHub

```bash
# Tag a versão
git tag v1.0.0
git push origin v1.0.0

# Criar release no GitHub e anexar os arquivos dist/*
```

### 2. Instalação pelos Usuários

```bash
pip install git+https://github.com/yourusername/os-backup.git
osbackup --help
```

## Opção 3: Distribuição Direta

### 1. Criar Wheel

```bash
python -m build
# Compartilhar o arquivo dist/os_backup_cli-1.0.0-py3-none-any.whl
```

### 2. Instalação pelos Usuários

```bash
pip install os_backup_cli-1.0.0-py3-none-any.whl
osbackup --help
```

## Checklist Pré-Publicação

- [ ] Atualizar version em setup.py
- [ ] Atualizar README.md com instruções de instalação
- [ ] Testar instalação local com `pip install -e .`
- [ ] Testar todos os comandos da CLI
- [ ] Verificar dependências em requirements.txt
- [ ] Adicionar licença apropriada (LICENSE file)
- [ ] Criar CHANGELOG.md
- [ ] Testar em ambiente limpo

## Comandos Disponíveis Após Instalação

```bash
osbackup backup --host-id 1        # Fazer backup
osbackup hosts                      # Listar servidores
osbackup history --limit 20        # Ver histórico
osbackup logs <backup_id>          # Ver logs
osbackup status                     # Status atual
osbackup genkey                     # Gerar chave
osbackup restore <file> <output>   # Restaurar backup
```

## Notas Importantes

1. **Configuração**: Usuários precisarão configurar:
   - Variáveis de ambiente (.env)
   - Google Drive credentials (credentials.json)
   - Chave de criptografia (via `osbackup genkey`)

2. **Web Interface**: A interface web não é incluída na CLI package. Para incluí-la, considere criar um segundo pacote `os-backup-web`.

3. **Banco de Dados**: O SQLite database será criado automaticamente no diretório do usuário.

4. **Atualizações**: Para publicar novas versões:
   ```bash
   # Atualizar version em setup.py
   python -m build
   twine upload dist/*
   ```
