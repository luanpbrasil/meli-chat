"""
Script simples para ingestão dos dados CSV no SQLite - POC Meli Vision
"""

import pandas as pd
import sqlite3

# Configuração
DATA_DIR = "dados"
DB_PATH = "meli_vision.db"

# Mapeamento CSV -> Tabela
files = {
    "produtos.csv": "produtos",
    "clientes.csv": "clientes", 
    "vendas.csv": "vendas",
    "campanhas.csv": "campanhas",
    "estoque_movimentacoes.csv": "estoque_movimentacoes",
    "metricas_performance.csv": "metricas_performance"
}

def ingest_data():
    """Carrega todos os CSVs no banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    
    for csv_file, table_name in files.items():
        file_path = f"{DATA_DIR}/{csv_file}"
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"✅ {table_name}: {len(df)} registros")
    
    conn.close()
    print(f"🎉 Banco criado: {DB_PATH}")

if __name__ == "__main__":
    ingest_data()
