# 💰 Financias CDD

Aplicação de gerenciamento e análise de extratos bancários, desenvolvida com **Python, Streamlit, Pandas e PostgreSQL (Neon)**.

## 1. Criar ambiente virtual

Na raiz do projeto:

**Linux / Ubuntu / WSL**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar dependências

Com o ambiente virtual ativado:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Configurar banco de dados

Crie um arquivo `.env` na raiz do projeto:

```env
PGHOST=seu-host.neon.tech
PGDATABASE=neondb
PGUSER=seu_usuario
PGPASSWORD=sua_senha
PGSSLMODE=require
PGCHANNELBINDING=require
```

Utilize as credenciais fornecidas pelo Neon.

**Importante:** nunca compartilhe ou envie o arquivo `.env` para o GitHub. Confirme que ele está no `.gitignore`.

## 4. Testar conexão com o Neon

```bash
python -c "from api.health import testar_conexao; print(testar_conexao())"
```

O resultado esperado deve indicar `status: Conectado`.

## 5. Executar o projeto

```bash
streamlit run app.py
```

Acesse pelo navegador:

```text
http://localhost:8501
```

## 6. Solução de problemas

**Erro `externally-managed-environment`**

Verifique se o ambiente virtual está ativo e execute:

```bash
python -m pip --version
python -m pip install -r requirements.txt
```

Se necessário, recrie o ambiente virtual:

**Linux / Ubuntu / WSL**
```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows PowerShell**
```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Porta 8501 ocupada**

```bash
streamlit run app.py --server.port 8502
```

## 7. Execução diária

Depois da configuração inicial, basta:

```bash
source .venv/bin/activate
streamlit run app.py
```

Para encerrar a aplicação, pressione `Ctrl + C` no terminal.

Para sair do ambiente virtual:

```bash
deactivate
```
