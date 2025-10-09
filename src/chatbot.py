"""
Chatbot Q&A Analítico para Mercado Livre - POC
Usa LangChain SQL Agent com OpenAI para responder perguntas sobre dados de vendedor
"""

import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
try:
    from . import db
except ImportError:
    import db


class PlotGeneratorInput(BaseModel):
    """Input for plot generator tool."""
    python_code: str = Field(description="Python code to generate a plotly chart")


class PlotGeneratorTool(BaseTool):
    """Tool that executes Python code to generate plotly charts."""
    name: str = "plot_generator"
    description: str = """
    Use this tool to generate interactive charts and visualizations.
    
    The input should be Python code that:
    1. Queries the database using pandas.read_sql_query(sql, conn)
    2. Creates a plotly chart (px.bar, px.line, px.pie, etc.)
    3. Assigns the chart to variable 'fig'
    4. Closes the database connection
    
    Available libraries: pandas as pd, plotly.express as px, plotly.graph_objects as go, sqlite3
    Database file: 'meli_vision.db'
    
    Example:
    ```python
    import pandas as pd
    import plotly.express as px
    import sqlite3
    
    conn = sqlite3.connect('meli_vision.db')
    df = pd.read_sql_query("SELECT categoria, COUNT(*) as count FROM produtos GROUP BY categoria", conn)
    conn.close()
    fig = px.bar(df, x='categoria', y='count', title='Produtos por Categoria')
    ```
    
    Always assign the final chart to 'fig' variable and close database connections.
    """
    args_schema: Type[BaseModel] = PlotGeneratorInput
    last_figure: object = None  # Add as a Pydantic field
    
    def _run(self, python_code: str) -> str:
        """Execute the Python code to generate a chart."""
        try:
            print(f"🎨 Executando código Python para gerar gráfico...")
            print(f"📝 Código: {python_code}")
            
            # Create safe execution environment
            import pandas as pd
            import plotly.express as px
            import plotly.graph_objects as go
            import sqlite3
            
            # Define available variables for the code
            local_vars = {
                'pd': pd,
                'px': px, 
                'go': go,
                'sqlite3': sqlite3,
                'fig': None
            }
            
            # Create a safe globals environment
            safe_globals = {
                '__builtins__': {
                    '__import__': __import__,
                    'len': len,
                    'range': range,
                    'enumerate': enumerate,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'print': print,
                }
            }
            
            # Execute the code
            exec(python_code, safe_globals, local_vars)
            
            # Get the figure object
            fig = local_vars.get('fig')
            if fig:
                # Store figure for later retrieval
                self.last_figure = fig
                print("✅ Gráfico gerado com sucesso!")
                return "Chart generated successfully! The interactive chart will be displayed below the response."
            else:
                print("❌ Nenhuma figura foi criada")
                return "Error: No figure object was created. Make sure your code assigns the chart to 'fig' variable."
                
        except Exception as e:
            error_msg = f"Error generating chart: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _arun(self, python_code: str):
        raise NotImplementedError("This tool does not support async execution.")


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
        self.plot_tool = None
        
        # Palavras-chave para detectar solicitações de gráfico
        self.chart_keywords = [
            'gráfico', 'grafico', 'chart', 'plot', 'visualiz', 'mostrar',
            'plotar', 'desenhar', 'criar gráfico', 'fazer gráfico', 'mostrar graficamente'
        ]
        
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
        """Configura o SQL Agent do LangChain com ferramenta de plotagem"""
        try:
            # Criar toolkit SQL
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            
            # Criar ferramenta de plotagem
            self.plot_tool = PlotGeneratorTool()
            
            # Criar agent SQL com ferramenta de plotagem
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                extra_tools=[self.plot_tool],
                agent_type=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                max_iterations=5
            )
            
            print("✅ SQL Agent configurado com ferramenta de plotagem!")
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
    
    def _detect_chart_request(self, question):
        """Detecta se a pergunta solicita um gráfico"""
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in self.chart_keywords)
    
    
    def ask_with_chart(self, question):
        """
        Versão aprimorada que pode gerar gráficos via agent code generation
        
        Args:
            question: Pergunta em português sobre os dados
            
        Returns:
            Dict com 'response' (texto) e opcionalmente 'chart' (plotly figure)
        """
        if not self.agent:
            return {"response": "❌ Chatbot não inicializado. Execute initialize() primeiro."}
        
        result = {"response": "", "chart": None}
        
        try:
            print(f"\n🤔 Pergunta: {question}")
            
            # Verificar se é solicitação de gráfico
            needs_chart = self._detect_chart_request(question)
            
            if needs_chart:
                # Modificar pergunta para solicitar geração de código Python
                enhanced_question = f"""
                {question}
                
                Por favor, use a ferramenta plot_generator para criar um gráfico interativo. 
                Escreva código Python que:
                1. Conecte ao banco 'meli_vision.db'
                2. Execute a consulta SQL apropriada
                3. Crie um gráfico plotly adequado (bar, line, pie, etc.)
                4. Atribua o gráfico à variável 'fig'
                5. Feche a conexão do banco
                
                Escolha o tipo de gráfico mais apropriado para os dados.
                """
            else:
                enhanced_question = question
            
            # Obter resposta do agente
            try:
                response = self.agent.run(enhanced_question)
            except Exception as agent_error:
                print(f"⚠️ Erro com agente: {agent_error}")
                response = self.agent.invoke({"input": enhanced_question})
                if isinstance(response, dict) and "output" in response:
                    response = response["output"]
            
            result["response"] = response
            
            # Verificar se gráfico foi gerado pelo plot_tool
            if needs_chart and self.plot_tool and hasattr(self.plot_tool, 'last_figure') and self.plot_tool.last_figure:
                result["chart"] = self.plot_tool.last_figure
                # Limpar a figura para próximo uso
                self.plot_tool.last_figure = None
                print("✅ Gráfico capturado do plot_tool!")
            
            print(f"🤖 Resposta: {result['response'][:200]}...")
            return result
            
        except Exception as e:
            error_msg = f"❌ Erro ao processar pergunta: {e}"
            print(error_msg)
            return {"response": error_msg, "chart": None}
    
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
