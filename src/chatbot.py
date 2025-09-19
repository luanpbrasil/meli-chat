"""
Chatbot Q&A Analítico para Mercado Livre - POC
Usa LangChain SQL Agent com OpenAI para responder perguntas sobre dados de vendedor
"""

import os
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
import db


class MeliChatbot:
    def __init__(self, openai_api_key=None, model="gpt-5-mini-2025-08-07"):
        """
        Inicializa o chatbot
        
        Args:
            openai_api_key: Chave da API OpenAI (ou use variável de ambiente OPENAI_API_KEY)
            model: Modelo OpenAI a usar (default: gpt-3.5-turbo)
        """
        self.db_path = "meli_vision.db"
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.db = None
        self.llm = None
        self.agent = None
        
    def ensure_database(self):
        """Garante que o banco de dados existe, criando se necessário"""
        if not Path(self.db_path).exists():
            print("🗄️ Banco não encontrado. Criando...")
            db.ingest_data()
        
        # Conectar ao banco via LangChain
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        print(f"✅ Conectado ao banco: {self.db_path}")
        
        # Verificar tabelas disponíveis
        tables = self.db.get_usable_table_names()
        print(f"📊 Tabelas disponíveis: {tables}")
        
        return True
    
    def setup_llm(self):
        """Configura o modelo OpenAI"""
        try:
            # Verificar se a API key foi fornecida
            if not self.openai_api_key:
                print("⚠️ API Key da OpenAI não especificada.")
                print("💡 Configure OPENAI_API_KEY como variável de ambiente ou passe no construtor.")
                return False
            
            # Configurar ChatOpenAI
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model=self.model,
                temperature=0,
                max_tokens=2000
            )
            
            print(f"✅ Modelo OpenAI configurado: {self.model}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar modelo OpenAI: {e}")
            return False
    
    def setup_agent(self):
        """Configura o SQL Agent do LangChain"""
        try:
            # Criar toolkit SQL
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            
            # Criar agent SQL
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                agent_type=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                max_iterations=5
            )
            
            print("✅ SQL Agent configurado!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar SQL Agent: {e}")
            return False
    
    def initialize(self):
        """Inicializa todos os componentes do chatbot"""
        print("🤖 Inicializando Meli Chatbot...")
        
        if not self.ensure_database():
            return False
            
        if not self.setup_llm():
            print("⚠️ Não foi possível configurar modelo OpenAI")
            return False
            
        if not self.setup_agent():
            return False
        
        print("🎉 Chatbot pronto para uso!")
        return True
    
    def ask(self, question):
        """
        Faz uma pergunta ao chatbot
        
        Args:
            question: Pergunta em português sobre os dados
            
        Returns:
            Resposta do chatbot
        """
        if not self.agent:
            return "❌ Chatbot não inicializado. Execute initialize() primeiro."
        
        try:
            print(f"\n🤔 Pergunta: {question}")
            
            # Tentar com o agente principal
            try:
                response = self.agent.run(question)
            except Exception as agent_error:
                print(f"⚠️ Erro com agente: {agent_error}")
                # Fallback: usar invoke se run não funcionar
                response = self.agent.invoke({"input": question})
                if isinstance(response, dict) and "output" in response:
                    response = response["output"]
            
            print(f"🤖 Resposta: {response}")
            return response
            
        except Exception as e:
            error_msg = f"❌ Erro ao processar pergunta: {e}"
            print(error_msg)
            return error_msg
    
    def show_schema(self):
        """Mostra o esquema das tabelas para referência"""
        # Garantir que o banco existe
        self.ensure_database()
        
        if not self.db:
            print("❌ Banco não conectado")
            return
        
        print("\n📋 Esquema do Banco de Dados:")
        print("=" * 50)
        
        for table in self.db.get_usable_table_names():
            print(f"\n🗂️ Tabela: {table}")
            try:
                # Usar a estrutura do banco LangChain
                table_info = self.db.get_table_info_no_throw([table])
                print(f"  📝 {table_info}")
                
            except Exception as e:
                print(f"  ❌ Erro: {e}")


def demo_questions():
    """Exemplos de perguntas que o chatbot pode responder"""
    questions = [
        "Quantos produtos temos cadastrados?",
        "Qual foi o faturamento total em janeiro de 2024?",
        "Quais são os 5 produtos mais caros?",
        "Quantas vendas foram feitas até agora?",
        "Qual é a média de preço dos produtos?",
        "Quais campanhas estão ativas?",
        "Qual cliente comprou mais vezes?",
        "Qual categoria de produto vende mais?",
        "Como está o estoque dos produtos?",
        "Qual foi a venda de maior valor?"
    ]
    
    print("\n💡 Exemplos de perguntas:")
    print("=" * 40)
    for i, q in enumerate(questions, 1):
        print(f"{i:2d}. {q}")


def main():
    """Função principal - demonstração do chatbot"""
    print("🎯 Meli Vision - Chatbot Analítico")
    print("=" * 50)
    
    # Criar instância do chatbot
    chatbot = MeliChatbot()
    
    # Mostrar esquema do banco (cria se não existir)
    chatbot.show_schema()
    
    # Mostrar exemplos de perguntas
    demo_questions()


if __name__ == "__main__":
    main()
