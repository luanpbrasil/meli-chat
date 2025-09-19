"""
Meli Vision Chatbot - Interface Streamlit
Chatbot Q&A Analítico para dados de vendedor do Mercado Livre
"""

import streamlit as st
import os
from chatbot import MeliChatbot
import time

# Configuração da página
st.set_page_config(
    page_title="Meli Vision - Chatbot Analítico",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FFE600;
        background: linear-gradient(90deg, #3483FA, #00A650);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .sidebar-info {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inicializa o estado da sessão"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    
    if "chatbot_initialized" not in st.session_state:
        st.session_state.chatbot_initialized = False

def initialize_chatbot(api_key, model):
    """Inicializa o chatbot com a API key e modelo fornecidos"""
    with st.spinner("🤖 Inicializando chatbot..."):
        try:
            # Criar instância do chatbot
            chatbot = MeliChatbot(openai_api_key=api_key, model=model)
            
            # Inicializar (cria banco se necessário)
            if chatbot.initialize():
                st.session_state.chatbot = chatbot
                st.session_state.chatbot_initialized = True
                st.success("✅ Chatbot conectado com sucesso!")
                
                # Adicionar mensagem de boas-vindas se for a primeira vez
                if not st.session_state.messages:
                    welcome_msg = f"Olá! Sou seu assistente analítico conectado com {model}. Como posso ajudar você com os dados do Mercado Livre?"
                    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
                
                st.rerun()
            else:
                st.error("❌ Falha na inicialização do chatbot")
                
        except Exception as e:
            st.error(f"❌ Erro ao inicializar: {str(e)}")
            st.session_state.chatbot_initialized = False

def process_user_question(question):
    """Processa uma pergunta do usuário e gera resposta"""
    if st.session_state.chatbot_initialized and st.session_state.chatbot:
        try:
            # Gerar resposta usando o chatbot
            with st.spinner("🤔 Processando pergunta..."):
                response = st.session_state.chatbot.ask(question)
                st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            error_msg = f"❌ Erro ao processar pergunta: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

def setup_sidebar():
    """Configura a barra lateral"""
    with st.sidebar:
        st.markdown("## ⚙️ Configuração")
        
        # Configuração da API Key
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Insira sua chave da API OpenAI ou configure como variável de ambiente OPENAI_API_KEY"
        )
        
        # Seleção do modelo
        model = st.selectbox(
            "Modelo OpenAI",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o-mini"],
            index=0,
            help="Escolha o modelo OpenAI para o chatbot"
        )
        
        # Auto-inicialização do chatbot quando API key está disponível
        if api_key and not st.session_state.chatbot_initialized:
            if st.button("🚀 Conectar", type="primary"):
                initialize_chatbot(api_key, model)
        elif api_key and st.session_state.chatbot_initialized:
            # Reconectar se modelo mudou
            current_model = getattr(st.session_state.chatbot, 'model', '')
            if current_model != model:
                if st.button("🔄 Reconectar", type="secondary"):
                    st.session_state.chatbot_initialized = False
                    initialize_chatbot(api_key, model)
        
        # Status do chatbot
        if st.session_state.chatbot_initialized:
            st.markdown('🟢 <b>Chatbot Conectado</b>', unsafe_allow_html=True)
            if hasattr(st.session_state.chatbot, 'model'):
                st.markdown(f'<small>Modelo: {st.session_state.chatbot.model}</small>', unsafe_allow_html=True)
        elif api_key:
            st.markdown('🟡 <b>Pronto para Conectar</b>', unsafe_allow_html=True)
        else:
            st.markdown('🔴 <b>API Key Necessária</b>', unsafe_allow_html=True)
        
        # Botão para limpar chat
        if st.button("🗑️ Limpar Chat"):
            st.session_state.messages = []
            st.rerun()
        
        # Informações do banco
        st.markdown("---")
        st.markdown("## 📊 Banco de Dados")
        st.markdown("""
        **Tabelas disponíveis:**
        - 📦 produtos
        - 👥 clientes  
        - 💰 vendas
        - 📈 campanhas
        - 📋 estoque_movimentacoes
        - 📊 metricas_performance
        """)
        
        # Exemplos de perguntas
        st.markdown("---")
        st.markdown("## 💡 Exemplos de Perguntas")
        
        example_questions = [
            "Quantos produtos temos?",
            "Qual foi o faturamento em janeiro?",
            "Quais os produtos mais caros?",
            "Quantas vendas foram feitas?",
            "Qual cliente comprou mais?",
            "Campanhas ativas?",
            "Média de preço dos produtos?"
        ]
        
        for i, question in enumerate(example_questions):
            if st.button(f"📝 {question}", key=f"example_{i}", disabled=not st.session_state.chatbot_initialized):
                # Adicionar pergunta do usuário
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Processar resposta imediatamente
                process_user_question(question)
                st.rerun()

def display_chat_messages():
    """Exibe as mensagens do chat"""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message">
                <b>🤔 Você:</b> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message">
                <b>🤖 Assistente:</b> {message["content"]}
            </div>
            """, unsafe_allow_html=True)

def display_table_data(table_name, num_rows=10):
    """Exibe os dados de uma tabela selecionada"""
    try:
        import sqlite3
        import pandas as pd
        
        # Conectar ao banco
        conn = sqlite3.connect("meli_vision.db")
        
        # Buscar dados da tabela
        query = f"SELECT * FROM {table_name} LIMIT {num_rows}"
        df = pd.read_sql_query(query, conn)
        
        # Buscar total de registros
        count_query = f"SELECT COUNT(*) as total FROM {table_name}"
        total_records = pd.read_sql_query(count_query, conn).iloc[0]['total']
        
        conn.close()
        
        # Exibir informações da tabela
        st.markdown(f"### 📋 Tabela: {table_name}")
        st.markdown(f"**Total de registros:** {total_records} | **Mostrando:** {len(df)} primeiros")
        
        # Exibir tabela
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar tabela {table_name}: {str(e)}")
        st.info("💡 Certifique-se de que o banco de dados foi criado executando db.py")

def main():
    """Função principal da aplicação"""
    # Inicializar estado da sessão
    init_session_state()
    
    # Cabeçalho principal
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Meli Vision - Chatbot Analítico</h1>
        <p>Seu assistente inteligente para análise de dados do Mercado Livre</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configurar barra lateral
    setup_sidebar()
    
    # Seção de visualização de tabelas
    st.markdown("## 📊 Visualizar Dados")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Seletor de tabela
        table_options = ["Nenhuma", "produtos", "clientes", "vendas", "campanhas", "estoque_movimentacoes", "metricas_performance"]
        selected_table = st.selectbox(
            "Selecione uma tabela para visualizar:",
            table_options,
            key="table_selector"
        )
        
        # Resetar estado se mudou a tabela
        if "last_selected_table" not in st.session_state:
            st.session_state.last_selected_table = "Nenhuma"
        
        if st.session_state.last_selected_table != selected_table:
            st.session_state.show_table = False
            st.session_state.last_selected_table = selected_table
    
    with col2:
        # Botão para mostrar/esconder tabela
        if "show_table" not in st.session_state:
            st.session_state.show_table = False
        
        if selected_table != "Nenhuma":
            if st.button("👁️ Mostrar" if not st.session_state.show_table else "🙈 Esconder"):
                st.session_state.show_table = not st.session_state.show_table
    
    with col3:
        # Número de linhas para mostrar
        if selected_table != "Nenhuma" and st.session_state.show_table:
            num_rows = st.number_input("Linhas:", min_value=5, max_value=100, value=10, step=5)
    
    # Mostrar tabela se selecionada
    if selected_table != "Nenhuma" and st.session_state.show_table:
        display_table_data(selected_table, num_rows if 'num_rows' in locals() else 10)
    
    # Área principal do chat
    st.markdown("---")
    st.markdown("## 💬 Chat")
    
    # Container para mensagens
    chat_container = st.container()
    
    with chat_container:
        # Exibir mensagens existentes
        display_chat_messages()
        
        # Mensagem de boas-vindas
        if not st.session_state.messages:
            if st.session_state.chatbot_initialized:
                welcome_msg = "Olá! Estou conectado e pronto para ajudar com análises dos dados do Mercado Livre. Faça sua pergunta!"
            else:
                welcome_msg = "Olá! Configure sua API Key da OpenAI na barra lateral e clique em 'Conectar' para começar!"
            
            st.markdown(f"""
            <div class="chat-message">
                <b>🤖 Assistente:</b> {welcome_msg}
            </div>
            """, unsafe_allow_html=True)
    
    # Input para nova mensagem
    if prompt := st.chat_input("Digite sua pergunta aqui...", disabled=not st.session_state.chatbot_initialized):
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Processar pergunta
        process_user_question(prompt)
        
        # Recarregar para mostrar nova mensagem
        st.rerun()
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        🛠️ Desenvolvido com Streamlit | 🤖 Powered by OpenAI | 📊 Dados do Mercado Livre
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
