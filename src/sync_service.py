"""
Serviço de Sincronização MongoDB -> PostgreSQL
"""
import streamlit as st
import pymongo
import os
from datetime import datetime
from bson import ObjectId
import pandas as pd
from src.postgres_service import PostgreSQLService

class SyncService:
    def __init__(self):
        self.mongodb_client = None
        self.postgres_service = None
        self.init_connections()
    
    def init_connections(self):
        """Inicializa conexões MongoDB e PostgreSQL"""
        try:
            # MongoDB
            mongodb_uri = os.getenv('MONGODB_URI')
            if mongodb_uri:
                self.mongodb_client = pymongo.MongoClient(mongodb_uri)
                self.mongodb_db = self.mongodb_client.fox
            
            # PostgreSQL
            self.postgres_service = PostgreSQLService()
            
        except Exception as e:
            st.error(f"❌ Erro ao inicializar conexões: {str(e)}")
    
    def get_mongodb_cargas(self):
        """Busca dados de cargas do MongoDB"""
        try:
            if not self.mongodb_client:
                return pd.DataFrame()
            
            # Pipeline para buscar dados de cargas
            pipeline = [
                {"$match": {"createdAt": {"$gte": datetime(2025, 1, 1)}, "status": {"$ne": "Cancelado"}}},
                {
                    "$lookup": {
                        "from": "orderv2",
                        "localField": "destinationOrder",
                        "foreignField": "_id",
                        "as": "destination_info"
                    }
                },
                {
                    "$lookup": {
                        "from": "orderv2",
                        "localField": "originOrder", 
                        "foreignField": "_id",
                        "as": "origin_info"
                    }
                },
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "destination_info.buyer",
                        "foreignField": "_id",
                        "as": "buyer_info"
                    }
                },
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "origin_info.seller",
                        "foreignField": "_id", 
                        "as": "seller_info"
                    }
                },
                {
                    "$lookup": {
                        "from": "grains",
                        "localField": "destination_info.grain",
                        "foreignField": "_id",
                        "as": "grain_info"
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "amount": 1,
                        "loadingDate": 1,
                        "status": 1,
                        "paid": 1,
                        "createdAt": 1,
                        "buyer_name": {"$arrayElemAt": ["$buyer_info.name", 0]},
                        "seller_name": {"$arrayElemAt": ["$seller_info.name", 0]},
                        "grain_name": {"$arrayElemAt": ["$grain_info.name", 0]},
                        "contract_type": {
                            "$cond": {
                                "if": {"$ne": ["$originOrder", None]},
                                "then": "🌾 Grão",
                                "else": "🚛 Frete"
                            }
                        }
                    }
                },
                {"$sort": {"loadingDate": -1}},
                {"$limit": 1000}
            ]
            
            results = list(self.mongodb_db.ticketv2.aggregate(pipeline))
            
            if not results:
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(results)
            
            # Calcular valores financeiros (placeholder)
            df['receita'] = df['amount'].fillna(0) * 50
            df['custo'] = df['amount'].fillna(0) * 30
            df['frete'] = df['amount'].fillna(0) * 10
            df['lucro_bruto'] = df['receita'] - df['custo'] - df['frete']
            
            return df
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar dados MongoDB: {str(e)}")
            return pd.DataFrame()
    
    def sync_data(self):
        """Executa sincronização completa"""
        try:
            # Verificar se PostgreSQL está disponível
            if not self.postgres_service or not self.postgres_service.connection:
                return False, "PostgreSQL não está disponível"
            
            # Buscar dados do MongoDB
            st.info("🔄 Buscando dados do MongoDB...")
            mongodb_data = self.get_mongodb_cargas()
            
            if mongodb_data.empty:
                return False, "Nenhum dado encontrado no MongoDB"
            
            # Sincronizar para PostgreSQL
            st.info("🔄 Sincronizando para PostgreSQL...")
            synced_count = self.postgres_service.sync_from_mongodb(mongodb_data)
            
            if synced_count > 0:
                return True, f"✅ {synced_count} registros sincronizados com sucesso!"
            else:
                return False, "Erro na sincronização"
                
        except Exception as e:
            return False, f"❌ Erro na sincronização: {str(e)}"
    
    def get_sync_status(self):
        """Retorna status da sincronização"""
        try:
            # Stats MongoDB
            mongodb_count = 0
            if self.mongodb_client:
                mongodb_count = self.mongodb_db.ticketv2.count_documents({
                    "createdAt": {"$gte": datetime(2025, 1, 1)},
                    "status": {"$ne": "Cancelado"}
                })
            
            # Stats PostgreSQL
            postgres_stats = self.postgres_service.get_sync_stats()
            
            return {
                'mongodb_count': mongodb_count,
                'postgres_count': postgres_stats['total_cargas'],
                'last_sync': postgres_stats['last_sync'],
                'sync_needed': mongodb_count != postgres_stats['total_cargas']
            }
            
        except Exception as e:
            st.error(f"❌ Erro ao verificar status: {str(e)}")
            return {
                'mongodb_count': 0,
                'postgres_count': 0,
                'last_sync': None,
                'sync_needed': True
            }
    
    def close_connections(self):
        """Fecha todas as conexões"""
        if self.mongodb_client:
            self.mongodb_client.close()
        if self.postgres_service:
            self.postgres_service.close()

