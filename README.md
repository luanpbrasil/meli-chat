# Meli Vision - Chatbot Analítico

Um chatbot inteligente para análise de dados do Mercado Livre usando IA.

## 📝 Sobre o Projeto

O Meli Vision é um assistente analítico que permite fazer perguntas em linguagem natural sobre dados de vendas, produtos, clientes e campanhas do Mercado Livre. O chatbot usa modelos da OpenAI para interpretar suas perguntas e gerar consultas SQL automaticamente.

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Streamlit** - Interface web interativa
- **LangChain** - Framework para integração com LLMs
- **OpenAI GPT** - Modelos de linguagem para análise
- **SQLite** - Banco de dados local
- **Pandas** - Manipulação de dados
- **Docker** - Containerização

## 📊 Dados Incluídos

- Produtos
- Clientes  
- Vendas
- Campanhas
- Movimentações de estoque
- Métricas de performance

## 🚀 Como Executar

### Método 1: Docker (Recomendado)

1. Configure sua chave da OpenAI:
```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

2. Execute com Docker:
```bash
docker-compose up --build
```

3. Acesse: http://localhost:8501

### Método 2: Ambiente Local

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure a chave da API:
```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

3. Execute a aplicação:
```bash
cd src
streamlit run app.py
```

## 💡 Exemplos de Perguntas

- "Quantos produtos temos no catálogo?"
- "Qual foi o faturamento do mês passado?"
- "Quais são os produtos mais vendidos?"
- "Quantos clientes únicos fizemos vendas?"
- "Qual campanha teve melhor performance?"

## 🔧 Configuração

1. Obtenha uma chave da API da OpenAI em: https://platform.openai.com/
2. Configure a variável de ambiente `OPENAI_API_KEY`
3. Escolha o modelo desejado na interface (GPT-3.5, GPT-4, etc.)

## 📁 Estrutura do Projeto

```
meli-chat/
├── dados/           # Arquivos CSV com dados
├── src/             # Código fonte
│   ├── app.py       # Interface Streamlit  
│   ├── chatbot.py   # Lógica do chatbot
│   └── db.py        # Gestão do banco de dados
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```