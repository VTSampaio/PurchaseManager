# Sistema de Solicitação de Compras - Documentação Técnica

## Visão Geral
Sistema web para gerenciamento de solicitações de compras organizacionais, desenvolvido em Python Flask com banco PostgreSQL e autenticação via Replit.

## Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM para banco de dados
- **Flask-Login** - Gerenciamento de sessões
- **PostgreSQL** - Banco de dados
- **Pandas + OpenPyXL** - Processamento de Excel
- **Gunicorn** - Servidor WSGI

### Frontend
- **HTML5/CSS3/JavaScript**
- **Bootstrap 5** - Framework CSS responsivo
- **Font Awesome** - Ícones

### Autenticação
- **Replit Auth** - OpenID Connect
- **OAuth 2.0** com PKCE

## Estrutura do Projeto

```
├── app.py                 # Configuração principal da aplicação
├── main.py               # Ponto de entrada
├── models.py             # Modelos do banco de dados
├── routes.py             # Rotas e lógica de negócio
├── replit_auth.py        # Sistema de autenticação
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── request_form.html
│   ├── admin.html
│   ├── minhas_solicitacoes.html
│   └── 403.html
├── static/
│   ├── js/
│   │   └── main.js       # JavaScript do frontend
│   └── css/
│       └── custom.css    # Estilos customizados
└── pyproject.toml        # Dependências do projeto
```

## Banco de Dados

### Tabelas Principais

#### 1. users
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE,
    first_name VARCHAR,
    last_name VARCHAR,
    profile_image_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. purchase_requests
```sql
CREATE TABLE purchase_requests (
    id SERIAL PRIMARY KEY,
    numero_solicitacao VARCHAR(20) UNIQUE NOT NULL,
    requester_name VARCHAR(100) NOT NULL,
    requester_email VARCHAR(120),
    obra_id VARCHAR(50),
    responsavel VARCHAR(100),
    tipo_entrega VARCHAR(50),
    endereco_entrega TEXT,
    status VARCHAR(20) DEFAULT 'Pendente',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. request_items
```sql
CREATE TABLE request_items (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES purchase_requests(id),
    descricao_insumos VARCHAR(500) NOT NULL,
    qtd FLOAT NOT NULL,
    und VARCHAR(20) NOT NULL,
    periodo_locacao VARCHAR(100),
    demanda VARCHAR(100),
    data_entrega DATE,
    servico_cpu VARCHAR(100),
    cod_insumo VARCHAR(50),
    observacoes TEXT,
    status_item VARCHAR(20) DEFAULT 'Pendente'
);
```

#### 4. oauth (Sistema de Autenticação)
```sql
CREATE TABLE oauth (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    browser_session_key VARCHAR NOT NULL,
    provider VARCHAR NOT NULL,
    token JSON
);
```

## Funcionalidades Implementadas

### 1. Autenticação e Autorização
- Login via Replit (OpenID Connect)
- Controle de acesso baseado em roles
- Sessões seguras com tokens JWT
- Logout com invalidação de sessão

### 2. Dashboard Principal
- Estatísticas em tempo real
- Contadores de solicitações por status
- Interface responsiva

### 3. Sistema de Solicitações
- Formulário detalhado com validação
- Numeração automática (SOL-YYYY-MM-NNNN)
- Múltiplos itens por solicitação
- Upload de Excel com template

### 4. Painel Administrativo
- Listagem de todas as solicitações
- Filtros por status e data
- Atualização de status em lote
- Gerenciamento de itens individuais

### 5. Consulta de Solicitações
- "Minhas Solicitações" para usuários
- Rastreamento de status por item
- Histórico completo

### 6. Integração Excel
- Download de template pré-formatado
- Upload e processamento automático
- Validação de dados
- Preenchimento automático do formulário

## Segurança

### Medidas Implementadas
1. **Autenticação OAuth 2.0** com PKCE
2. **CSRF Protection** via Flask-WTF
3. **Validação de entrada** em todos os formulários
4. **Sanitização de dados** antes da inserção no banco
5. **Controle de acesso** por rotas protegidas
6. **Sessões seguras** com cookies HttpOnly

### Variáveis de Ambiente Necessárias
```bash
DATABASE_URL=postgresql://...
SESSION_SECRET=...
REPL_ID=...
ISSUER_URL=https://replit.com/oidc
```

## Instalação e Deploy

### Dependências
```bash
# Instalar dependências
pip install -r requirements.txt

# Ou usando uv (recomendado)
uv sync
```

### Configuração do Banco
```python
# As tabelas são criadas automaticamente na inicialização
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Execução
```bash
# Desenvolvimento
python main.py

# Produção
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## APIs e Endpoints

### Públicos
- `GET /` - Dashboard principal
- `GET /auth/login` - Login
- `GET /auth/logout` - Logout

### Protegidos (Requer Autenticação)
- `GET /request` - Formulário de nova solicitação
- `POST /submit_request` - Enviar solicitação
- `GET /minhas-solicitacoes` - Minhas solicitações
- `GET /admin` - Painel administrativo
- `POST /update_status/<id>` - Atualizar status
- `GET /download-template` - Download template Excel
- `POST /upload-excel` - Upload arquivo Excel

## Validações e Regras de Negócio

### Solicitações
1. Nome do solicitante é obrigatório
2. Pelo menos um item deve ser adicionado
3. Itens devem ter descrição, quantidade e unidade
4. Numeração automática sequencial
5. Status padrão: "Pendente"

### Upload Excel
1. Formato aceito: .xlsx, .xls
2. Colunas obrigatórias: Descrição, QTD, UND
3. Validação de tipos de dados
4. Tratamento de erros robusto

## Monitoramento e Logs

### Logs Implementados
- Inicialização da aplicação
- Criação de tabelas do banco
- Erros de autenticação
- Uploads de Excel
- Operações CRUD

### Métricas Disponíveis
- Total de solicitações
- Solicitações por status
- Performance de upload
- Erros de validação

## Backup e Recuperação

### Estratégia Recomendada
1. **Backup diário** do PostgreSQL
2. **Retenção** de 30 dias
3. **Backup de código** no Git
4. **Backup de uploads** se implementado

## Considerações de Performance

### Otimizações Implementadas
1. **Conexão pooling** do SQLAlchemy
2. **Lazy loading** para relacionamentos
3. **Índices** nas colunas de busca
4. **Paginação** para listagens grandes
5. **Cache de sessão** no banco

## Escalabilidade

### Pontos de Atenção
1. **Banco de dados** - Considerar read replicas
2. **Uploads** - Implementar storage externo (S3)
3. **Sessions** - Migrar para Redis em alta carga
4. **Load balancing** - Múltiplas instâncias da aplicação

## Testes Recomendados

### Testes Funcionais
1. Fluxo completo de solicitação
2. Upload e processamento de Excel
3. Autenticação e autorização
4. CRUD de solicitações
5. Validações de formulário

### Testes de Segurança
1. Injeção SQL
2. XSS (Cross-Site Scripting)
3. CSRF (Cross-Site Request Forgery)
4. Controle de acesso
5. Upload de arquivos maliciosos

### Testes de Performance
1. Carga simultânea de usuários
2. Upload de arquivos grandes
3. Consultas complexas no banco
4. Tempo de resposta das páginas

## Manutenção

### Tarefas Regulares
1. **Limpeza de sessões** expiradas
2. **Backup** do banco de dados
3. **Monitoramento** de logs de erro
4. **Atualização** de dependências
5. **Verificação** de espaço em disco

## Contato e Suporte

Para dúvidas técnicas ou problemas:
- Consultar logs da aplicação
- Verificar status do banco PostgreSQL
- Validar variáveis de ambiente
- Conferir conectividade com Replit Auth

---

**Desenvolvido em:** Python Flask  
**Versão:** 1.0.0  
**Data:** Dezembro 2024  
**Compatibilidade:** Python 3.11+, PostgreSQL 12+