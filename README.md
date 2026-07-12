# ASAC — Sistema de Controle de Materiais de Consumo

Sistema web para gestão de entradas, saídas e consultas de materiais de consumo da **ASAC — Associação Sorocabana de Atividades para Deficientes Visuais**, desenvolvido por um voluntário da entidade.

---

## Sobre o projeto

A ASAC é uma ONG sem fins lucrativos que atende pessoas com deficiência visual. Este sistema substitui o controle manual de estoque de materiais, permitindo que a equipe registre movimentações, acompanhe saldos e receba alertas de reposição de forma simples e acessível.

O frontend foi desenvolvido com atenção à acessibilidade (WCAG 2.1 AA), priorizando navegação completa por teclado e compatibilidade com leitores de tela (NVDA).

---

## Funcionalidades

- **Autenticação** com JWT e três níveis de acesso: Administrador, Operador e Consulta
- **Produtos** — cadastro, edição, desativação (soft delete) e alerta de estoque mínimo
- **Categorias** — organização dos produtos por tipo (Limpeza, Cozinha, Escritório etc.)
- **Movimentações** — registro de entradas, saídas, ajustes e descartes com histórico auditável
- **Usuários** — gestão de contas com desativação sem exclusão (RN-04)
- **Dashboard** — painel com indicadores de estoque e lista de produtos abaixo do mínimo
- **API REST** com documentação interativa gerada automaticamente pelo FastAPI

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 · FastAPI 0.115 · SQLAlchemy 2.0 |
| Banco de dados | SQLite |
| Autenticação | JWT (python-jose) · bcrypt |
| Frontend | HTML5 · CSS3 · JavaScript (vanilla) |
| Servidor | Uvicorn |

---

## Pré-requisitos

- Python 3.12+
- Git

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/fabriciogeog/asac-materiais.git
cd asac-materiais

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env             # edite o arquivo com sua SECRET_KEY
```

### Variáveis de ambiente (`.env`)

```env
DATABASE_URL=sqlite:///./asac.db
SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

> Gere uma `SECRET_KEY` segura com:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Inicialização

```bash
# Cria as tabelas e o usuário administrador inicial
python seed.py

# Sobe o servidor
uvicorn app.main:app --reload
```

Acesse **http://localhost:8000/ui/login.html** no navegador.

A documentação interativa da API está disponível em **http://localhost:8000/docs**.

---

## Acesso pela rede local com câmera (celular)

Navegadores só liberam a câmera (`getUserMedia`, usada no scanner de código de barras) em **contexto seguro**: HTTPS, ou `http://localhost`. Acessando pelo IP da rede local em HTTP puro (ex.: `http://192.168.0.10:8000`), a câmera não fica disponível — isso é regra do navegador, não limitação do sistema. Para usar o scanner pelo celular dentro do depósito, é preciso servir a aplicação via HTTPS.

### 1. Gerar certificado local com [mkcert](https://github.com/FiloSottile/mkcert)

```bash
sudo apt install mkcert libnss3-tools   # instala o mkcert e a dependência NSS
mkcert -install                          # cria e instala a CA local (pede senha sudo)

mkdir -p certs
mkcert -cert-file certs/cert.pem -key-file certs/key.pem \
  <IP_DA_REDE_LOCAL> localhost 127.0.0.1  # ex.: 192.168.0.10
```

A pasta `certs/` está no `.gitignore` — os certificados são gerados por máquina e nunca devem ser commitados.

### 2. Subir o servidor com HTTPS

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

Acesse do celular em `https://<IP_DA_REDE_LOCAL>:8000/ui/login.html`.

### 3. Confiar no certificado a partir do celular

O certificado é assinado pela CA local do mkcert, que o computador já confia — mas o celular ainda não. Transfira o arquivo `rootCA.pem` (mostrado por `mkcert -CAROOT`) para o celular (e-mail, Drive, cabo) e instale como certificado confiável:

- **Android**: Ajustes → Segurança → Criptografia e credenciais → Instalar um certificado → CA... e selecione o `rootCA.pem`.
- **iPhone**: instale o perfil e depois ative em Ajustes → Geral → Sobre → Configurações de confiança de certificado.

Feito isso uma vez por aparelho, o cadeado fica válido normalmente e a câmera passa a funcionar no Chrome e no Firefox do celular.

---

## Executar como serviço systemd (produção)

Em vez de subir o `uvicorn` manualmente num terminal (que fica preso à sessão e não sobrevive a reboot), use o serviço systemd em `systemd/asac.service`. Ele sobe com HTTPS (mesmos certificados do passo anterior), reinicia sozinho se cair e inicia junto com o sistema.

> **`.venv/` não é versionado** (está no `.gitignore`). Ao clonar/copiar o projeto para uma máquina nova, o serviço systemd vai falhar com `status=203/EXEC` até que o venv seja criado ali — veja o passo 0.
>
> **`systemd/asac.service` tem caminhos absolutos fixos** (`WorkingDirectory` e `ExecStart` apontam para `/home/fabricio/Projetos/Python/yolo-barcode`). Se o projeto for clonado do GitHub com outro nome de pasta (ex.: `asac-materiais`) ou em outro usuário/local, esses caminhos ficam errados e o serviço falha com o mesmo `status=203/EXEC` — mesmo que o `.venv` exista. Confira/edite os caminhos do arquivo antes de instalar (passo 1).

### 0. Criar o venv (uma vez por máquina, antes de instalar o serviço)

```bash
cd /caminho/do/projeto
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

O `ExecStart` do `asac.service` chama `.venv/bin/uvicorn` por caminho absoluto, então esse passo precisa rodar em toda máquina nova antes do serviço subir.

### 1. Instalar o serviço (uma vez por máquina)

Antes de copiar, confirme que `WorkingDirectory` e `ExecStart` em `systemd/asac.service` apontam para o caminho real onde o projeto foi clonado nessa máquina (pode ter nome de pasta diferente de `yolo-barcode`, dependendo de como o `git clone` foi feito):

```bash
grep -E "WorkingDirectory|ExecStart" systemd/asac.service
pwd    # compare com o caminho acima; edite o arquivo se divergir
```

```bash
sudo cp systemd/asac.service /etc/systemd/system/asac.service
sudo systemctl daemon-reload
sudo systemctl enable --now asac      # habilita no boot + inicia agora
```

### 2. Comandos do dia a dia

```bash
sudo systemctl status asac        # ver se está rodando
sudo systemctl restart asac       # reiniciar (ex.: depois de atualizar código)
sudo systemctl stop asac          # parar
journalctl -u asac -f             # acompanhar logs em tempo real
```

> Se o `systemd/asac.service` for editado (ex.: caminho do projeto mudou), repita `sudo cp` + `sudo systemctl daemon-reload` + `sudo systemctl restart asac`.

### Troubleshooting: `status=203/EXEC` no `journalctl`

Esse código indica que o systemd não conseguiu executar o binário do `ExecStart`. Causas mais comuns:

- **Nome da pasta do projeto diferente do que está no `asac.service`** — se o clone do GitHub usou outro nome (ex.: `asac-materiais` em vez de `yolo-barcode`), `WorkingDirectory`/`ExecStart` apontam para um caminho que não existe. Confira com `grep -E "WorkingDirectory|ExecStart" systemd/asac.service` e compare com `pwd`.
- **`.venv` não existe na máquina** (caso mais comum ao mover o projeto para uma máquina nova) — resolva com o passo 0 acima.
- Arquivo existe mas sem permissão de execução: `chmod +x .venv/bin/uvicorn`.
- Shebang do `.venv/bin/uvicorn` aponta para um python que não existe nessa máquina (`head -1 .venv/bin/uvicorn` para conferir o caminho).
- Partição com `noexec` no mount.

---

## Opção: implantar em VM (KVM)

Todos os passos acima assumem instalação direta na máquina (bare-metal), que é a forma padrão de rodar o sistema. Para quem preferir isolar o servidor numa máquina virtual — por exemplo, para testar com snapshots reversíveis ou rodar ao lado de outros serviços no mesmo computador — há um tutorial completo em [`docs/implantacao-vm.md`](docs/implantacao-vm.md), cobrindo KVM/QEMU + virt-manager, rede em bridge (para o celular acessar a VM na rede local), passthrough USB da webcam e a reaplicação dos passos de HTTPS/systemd dentro da VM.

---

## Estrutura do projeto

```
asac-materiais/
├── app/
│   ├── main.py            # Aplicação FastAPI, middlewares e montagem do frontend
│   ├── database.py        # Engine SQLAlchemy, sessão e Base declarativa
│   ├── auth.py            # Utilitários JWT e bcrypt
│   ├── deps.py            # Dependências: get_current_user, require_perfil
│   ├── models/            # Modelos ORM (Categoria, Produto, Usuario, Movimentacao)
│   ├── schemas/           # Schemas Pydantic (validação de entrada e saída)
│   └── routers/           # Endpoints REST por recurso
├── frontend/
│   ├── login.html
│   ├── index.html         # Dashboard
│   ├── produtos.html
│   ├── movimentacoes.html
│   ├── categorias.html
│   ├── usuarios.html
│   ├── css/style.css      # Folha de estilos acessível
│   └── js/
│       ├── api.js         # Wrapper de fetch com suporte a JWT
│       └── app.js         # Utilitários compartilhados (nav, notificações, guards)
├── systemd/
│   └── asac.service       # Unit systemd para rodar o servidor em produção
├── docs/
│   └── implantacao-vm.md  # Tutorial opcional: implantação em VM (KVM)
├── banco.sql              # Script SQL de criação das tabelas e seed de categorias
├── seed.py                # Script de inicialização do banco e criação do admin
└── requirements.txt
```

---

## Perfis de acesso

| Perfil | Categorias | Produtos | Movimentações | Usuários |
|--------|:----------:|:--------:|:-------------:|:--------:|
| Administrador | ✓ leitura/escrita | ✓ leitura/escrita | ✓ leitura/escrita | ✓ leitura/escrita |
| Operador | ✓ leitura/escrita | ✓ leitura/escrita | ✓ leitura/escrita | — |
| Consulta | ✓ somente leitura | ✓ somente leitura | ✓ somente leitura | — |

---

## Acessibilidade

O frontend foi desenvolvido para ser utilizável sem mouse, com foco especial em usuários de leitores de tela:

- Skip link "Ir para o conteúdo principal" em todas as páginas
- Atributos `aria-live`, `aria-current`, `aria-required` e `aria-invalid`
- Tabelas com `<caption>` e `<th scope="col">`
- Gerenciamento de foco após abertura e fechamento de formulários
- Contraste de cores em conformidade com WCAG 2.1 AA

---

## Documentos do projeto

- `ERS - Especificação de Requisitos de Software.pdf` — requisitos funcionais e não funcionais
- `Diagrama_Ajustado.png` — diagrama de classes UML
- `diagrama_classes.puml` — fonte PlantUML do diagrama

---

## Licença

Projeto desenvolvido para uso interno da ASAC. Todos os direitos reservados.
