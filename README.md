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
