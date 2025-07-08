"""
Serviço PostgreSQL para Sistema de Auditoria FOX
"""
import psycopg2
import pandas as pd
from datetime import datetime
import streamlit as st

class PostgreSQLService:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Conecta ao PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host="24.199.75.66",
                port=5432,
                user="myuser",
                password="mypassword",
                database="mydb"
            )
            return True
        except Exception as e:
            st.error(f"❌ Erro ao conectar PostgreSQL: {str(e)}")
            return False
    
    def create_tables(self):
        """Cria tabelas necessárias no PostgreSQL"""
        try:
            cursor = self.connection.cursor()
            
            # Tabela de cargas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cargas (
                    id SERIAL PRIMARY KEY,
                    ticket_id VARCHAR(255) UNIQUE,
                    amount DECIMAL(10,2),
                    loading_date TIMESTAMP,
                    status VARCHAR(100),
                    paid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    buyer_name VARCHAR(255),
                    seller_name VARCHAR(255),
                    grain_name VARCHAR(255),
                    contract_type VARCHAR(100),
                    receita DECIMAL(10,2),
                    custo DECIMAL(10,2),
                    frete DECIMAL(10,2),
                    lucro_bruto DECIMAL(10,2),
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao criar tabelas: {str(e)}")
            return False
    
    def get_cargas_data(self):
        """Busca dados de cargas do PostgreSQL"""
        try:
            query = """
                SELECT 
                    ticket_id,
                    loading_date,
                    buyer_name,
                    seller_name,
                    grain_name,
                    contract_type,
                    amount,
                    status,
                    paid,
                    receita,
                    custo,
                    frete,
                    lucro_bruto,
                    synced_at
                FROM cargas 
                WHERE loading_date >= '2025-01-01'
                ORDER BY loading_date DESC
                LIMIT 1000
            """
            
            df = pd.read_sql_query(query, self.connection)
            
            if not df.empty:
                # Processar dados
                df['data_carregamento'] = pd.to_datetime(df['loading_date']).dt.strftime('%d/%m/%Y')
                df['comprador'] = df['buyer_name'].fillna('N/A')
                df['vendedor'] = df['seller_name'].fillna('N/A')
                df['caminhoneiro'] = 'N/A'  # Placeholder
                df['grao'] = df['grain_name'].fillna('N/A')
                df['tipo_contrato'] = df['contract_type'].fillna('❓ Indefinido')
                df['quantidade'] = df['amount'].fillna(0)
                df['paid_status'] = df['paid'].apply(lambda x: '✅' if x else '⏰')
                
            return df
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar dados PostgreSQL: {str(e)}")
            return pd.DataFrame()
    
    def sync_from_mongodb(self, mongodb_data):
        """Sincroniza dados do MongoDB para PostgreSQL"""
        try:
            cursor = self.connection.cursor()
            
            # Limpar dados existentes
            cursor.execute("DELETE FROM cargas")
            
            # Inserir dados do MongoDB
            for _, row in mongodb_data.iterrows():
                cursor.execute("""
                    INSERT INTO cargas (
                        ticket_id, amount, loading_date, status, paid,
                        buyer_name, seller_name, grain_name, contract_type,
                        receita, custo, frete, lucro_bruto
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket_id) DO UPDATE SET
                        amount = EXCLUDED.amount,
                        loading_date = EXCLUDED.loading_date,
                        status = EXCLUDED.status,
                        paid = EXCLUDED.paid,
                        buyer_name = EXCLUDED.buyer_name,
                        seller_name = EXCLUDED.seller_name,
                        grain_name = EXCLUDED.grain_name,
                        contract_type = EXCLUDED.contract_type,
                        receita = EXCLUDED.receita,
                        custo = EXCLUDED.custo,
                        frete = EXCLUDED.frete,
                        lucro_bruto = EXCLUDED.lucro_bruto,
                        synced_at = CURRENT_TIMESTAMP
                """, (
                    str(row.get('_id', '')),
                    float(row.get('amount', 0)),
                    row.get('loadingDate'),
                    row.get('status', ''),
                    bool(row.get('paid', False)),
                    row.get('buyer_name', ''),
                    row.get('seller_name', ''),
                    row.get('grain_name', ''),
                    row.get('contract_type', ''),
                    float(row.get('receita', 0)),
                    float(row.get('custo', 0)),
                    float(row.get('frete', 0)),
                    float(row.get('lucro_bruto', 0))
                ))
            
            self.connection.commit()
            cursor.close()
            
            return len(mongodb_data)
            
        except Exception as e:
            st.error(f"❌ Erro na sincronização: {str(e)}")
            return 0
    
    def get_sync_stats(self):
        """Retorna estatísticas de sincronização"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cargas")
            total_cargas = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(synced_at) FROM cargas")
            last_sync = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'total_cargas': total_cargas,
                'last_sync': last_sync
            }
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar estatísticas: {str(e)}")
            return {'total_cargas': 0, 'last_sync': None}
    
    def close(self):
        """Fecha conexão"""
        if self.connection:
            self.connection.close()

