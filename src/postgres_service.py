"""
Serviço PostgreSQL para Sistema de Auditoria FOX
Usando pg8000 - biblioteca PostgreSQL pura em Python
Versão corrigida com criação automática de tabelas
"""
try:
    import pg8000
    PG8000_AVAILABLE = True
except ImportError:
    PG8000_AVAILABLE = False
    pg8000 = None

import pandas as pd
from datetime import datetime
import streamlit as st

class PostgreSQLService:
    def __init__(self):
        self.connection = None
        if PG8000_AVAILABLE:
            if self.connect():
                self.ensure_tables_exist()  # Garantir que tabelas existam
        else:
            st.error("❌ pg8000 não instalado. Execute: pip install pg8000")
    
    def connect(self):
        """Conecta ao PostgreSQL usando pg8000"""
        if not PG8000_AVAILABLE:
            return False
            
        try:
            self.connection = pg8000.connect(
                host="24.199.75.66",
                port=5432,
                user="myuser",
                password="mypassword",
                database="mydb"
            )
            st.success("✅ Conectado ao PostgreSQL com sucesso")
            return True
        except Exception as e:
            st.error(f"❌ Erro ao conectar PostgreSQL: {str(e)}")
            return False
    
    def ensure_tables_exist(self):
        """Garante que todas as tabelas necessárias existam"""
        if not PG8000_AVAILABLE or not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Verificar se tabela cargas existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'cargas'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                st.info("📋 Criando tabela 'cargas' no PostgreSQL...")
                self.create_cargas_table()
            else:
                st.success("✅ Tabela 'cargas' já existe no PostgreSQL")
            
            cursor.close()
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao verificar tabelas: {str(e)}")
            return False
    
    def create_cargas_table(self):
        """Cria a tabela de cargas no PostgreSQL"""
        if not PG8000_AVAILABLE or not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Criar tabela de cargas com todos os campos necessários
            create_table_sql = """
                CREATE TABLE cargas (
                    id SERIAL PRIMARY KEY,
                    ticket_id VARCHAR(255) UNIQUE NOT NULL,
                    amount DECIMAL(15,2) DEFAULT 0,
                    loading_date TIMESTAMP,
                    status VARCHAR(100) DEFAULT '',
                    paid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    buyer_name VARCHAR(255) DEFAULT '',
                    seller_name VARCHAR(255) DEFAULT '',
                    grain_name VARCHAR(255) DEFAULT '',
                    contract_type VARCHAR(100) DEFAULT '',
                    receita DECIMAL(15,2) DEFAULT 0,
                    custo DECIMAL(15,2) DEFAULT 0,
                    frete DECIMAL(15,2) DEFAULT 0,
                    lucro_bruto DECIMAL(15,2) DEFAULT 0,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            
            cursor.execute(create_table_sql)
            self.connection.commit()
            cursor.close()
            
            st.success("✅ Tabela 'cargas' criada com sucesso no PostgreSQL")
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao criar tabela 'cargas': {str(e)}")
            return False
    
    def table_exists(self):
        """Verifica se a tabela cargas existe"""
        if not PG8000_AVAILABLE or not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'cargas'
                )
            """)
            exists = cursor.fetchone()[0]
            cursor.close()
            return exists
        except Exception as e:
            st.error(f"❌ Erro ao verificar existência da tabela: {str(e)}")
            return False
    
    def get_cargas_data(self):
        """Busca dados de cargas do PostgreSQL"""
        if not PG8000_AVAILABLE or not self.connection:
            st.warning("⚠️ PostgreSQL não disponível")
            return pd.DataFrame()
            
        try:
            # Garantir que tabela existe antes de consultar
            if not self.table_exists():
                st.warning("⚠️ Tabela 'cargas' não existe. Criando...")
                if self.create_cargas_table():
                    st.info("📋 Tabela criada. Execute sincronização para popular dados.")
                return pd.DataFrame()  # Retorna vazio na primeira vez
            
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
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Buscar dados e colunas
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            
            # Criar DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            if not df.empty:
                # Processar dados para compatibilidade com interface
                df['data_carregamento'] = pd.to_datetime(df['loading_date']).dt.strftime('%d/%m/%Y')
                df['comprador'] = df['buyer_name'].fillna('N/A')
                df['vendedor'] = df['seller_name'].fillna('N/A')
                df['caminhoneiro'] = 'N/A'  # Placeholder
                df['grao'] = df['grain_name'].fillna('N/A')
                df['tipo_contrato'] = df['contract_type'].fillna('❓ Indefinido')
                df['quantidade'] = df['amount'].fillna(0)
                df['paid_status'] = df['paid'].apply(lambda x: '✅' if x else '⏰')
                
                # Adicionar colunas necessárias para interface
                df['nro_ticket'] = df['ticket_id']
                df['receita'] = df['receita'].fillna(0)
                df['custo'] = df['custo'].fillna(0)
                df['frete'] = df['frete'].fillna(0)
                df['lucro_bruto'] = df['lucro_bruto'].fillna(0)
            
            st.success(f"✅ {len(df)} cargas carregadas do PostgreSQL")
            return df
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar dados PostgreSQL: {str(e)}")
            return pd.DataFrame()
    
    def sync_from_mongodb(self, mongodb_data):
        """Sincroniza dados do MongoDB para PostgreSQL"""
        if not PG8000_AVAILABLE or not self.connection:
            st.error("❌ PostgreSQL não disponível para sincronização")
            return 0
            
        try:
            # Garantir que tabela existe
            if not self.table_exists():
                st.info("📋 Criando tabela antes da sincronização...")
                if not self.create_cargas_table():
                    return 0
            
            cursor = self.connection.cursor()
            
            # Limpar dados existentes
            cursor.execute("DELETE FROM cargas")
            st.info("🗑️ Dados antigos removidos do PostgreSQL")
            
            # Inserir dados do MongoDB
            inserted_count = 0
            for _, row in mongodb_data.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO cargas (
                            ticket_id, amount, loading_date, status, paid,
                            buyer_name, seller_name, grain_name, contract_type,
                            receita, custo, frete, lucro_bruto
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(row.get('_id', '')),
                        float(row.get('amount', 0)),
                        row.get('loadingDate'),
                        str(row.get('status', '')),
                        bool(row.get('paid', False)),
                        str(row.get('buyer_name', '')),
                        str(row.get('seller_name', '')),
                        str(row.get('grain_name', '')),
                        str(row.get('contract_type', '')),
                        float(row.get('receita', 0)),
                        float(row.get('custo', 0)),
                        float(row.get('frete', 0)),
                        float(row.get('lucro_bruto', 0))
                    ))
                    inserted_count += 1
                except Exception as row_error:
                    st.warning(f"⚠️ Erro ao inserir linha: {str(row_error)}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            st.success(f"✅ {inserted_count} cargas sincronizadas para PostgreSQL")
            return inserted_count
            
        except Exception as e:
            st.error(f"❌ Erro na sincronização: {str(e)}")
            return 0
    
    def get_sync_stats(self):
        """Retorna estatísticas de sincronização"""
        if not PG8000_AVAILABLE or not self.connection:
            return {'total_cargas': 0, 'last_sync': None}
            
        try:
            # Garantir que tabela existe
            if not self.table_exists():
                return {'total_cargas': 0, 'last_sync': None}
            
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cargas")
            total_cargas = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(synced_at) FROM cargas")
            last_sync_result = cursor.fetchone()
            last_sync = last_sync_result[0] if last_sync_result and last_sync_result[0] else None
            
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
            st.info("🔌 Conexão PostgreSQL fechada")

