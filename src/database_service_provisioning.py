"""
Extensão do DatabaseService para provisionamentos
"""
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from bson import ObjectId

from .data_models_provisioning import Provisioning, ProvisioningProcessor

class ProvisioningService:
    """Serviço para provisionamentos"""
    
    def __init__(self, collections):
        self.provisionings = collections['provisionings']
        self.users = collections['users']
        self.orderv2 = collections['orderv2']
    
    def get_provisionings(self, limit: int = 100) -> List[Provisioning]:
        """Busca provisionamentos"""
        try:
            cursor = self.provisionings.find().limit(limit).sort("createdAt", -1)
            provisionings = []
            
            for doc in cursor:
                provisioning = Provisioning(
                    _id=str(doc.get('_id')),
                    amount=doc.get('amount'),
                    amountRemaining=doc.get('amountRemaining'),
                    bagPrice=doc.get('bagPrice'),
                    createdAt=doc.get('createdAt'),
                    deliveryDeadline=doc.get('deliveryDeadline'),
                    deliveryDeadlineEnd=doc.get('deliveryDeadlineEnd'),
                    from_location=str(doc.get('from')) if doc.get('from') else None,
                    to_location=str(doc.get('to')) if doc.get('to') else None,
                    fullFreightPrice=doc.get('fullFreightPrice'),
                    grain=doc.get('grain'),
                    isFob=doc.get('isFob'),
                    isFreight=doc.get('isFreight'),
                    isGrain=doc.get('isGrain'),
                    paymentDaysAfterDelivery=doc.get('paymentDaysAfterDelivery'),
                    sellersOrders=doc.get('sellersOrders'),
                    updatedAt=doc.get('updatedAt'),
                    user=doc.get('user'),
                    order=str(doc.get('order')) if doc.get('order') else None,
                    pisCofins=doc.get('pisCofins'),
                    promotor=doc.get('promotor')
                )
                provisionings.append(provisioning)
            
            return provisionings
            
        except Exception as e:
            print(f"Erro ao buscar provisionamentos: {e}")
            return []
    
    def get_provisionings_with_users(self, limit: int = 100) -> List[Dict]:
        """Busca provisionamentos com lookup de users"""
        pipeline = [
            # Lookup com users para from
            {
                "$lookup": {
                    "from": "users",
                    "localField": "from",
                    "foreignField": "_id",
                    "as": "from_user_info"
                }
            },
            # Lookup com users para to
            {
                "$lookup": {
                    "from": "users",
                    "localField": "to",
                    "foreignField": "_id",
                    "as": "to_user_info"
                }
            },
            # Lookup com orderv2
            {
                "$lookup": {
                    "from": "orderv2",
                    "localField": "order",
                    "foreignField": "_id",
                    "as": "order_info"
                }
            },
            # Adicionar campos calculados
            {
                "$addFields": {
                    "from_user_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$from_user_info.name", 0]},
                            {"$arrayElemAt": ["$from_user_info.companyName", 0]}
                        ]
                    },
                    "to_user_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$to_user_info.name", 0]},
                            {"$arrayElemAt": ["$to_user_info.companyName", 0]}
                        ]
                    },
                    "valor_total": {
                        "$multiply": ["$amount", "$bagPrice"]
                    },
                    "valor_restante": {
                        "$multiply": ["$amountRemaining", "$bagPrice"]
                    },
                    "percentual_utilizado": {
                        "$cond": {
                            "if": {"$gt": ["$amount", 0]},
                            "then": {
                                "$multiply": [
                                    {"$divide": [
                                        {"$subtract": ["$amount", "$amountRemaining"]},
                                        "$amount"
                                    ]},
                                    100
                                ]
                            },
                            "else": 0
                        }
                    }
                }
            },
            {"$sort": {"createdAt": -1}},
            {"$limit": limit}
        ]
        
        try:
            results = list(self.provisionings.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Erro ao buscar provisionamentos com users: {e}")
            return []
    
    def get_provisionings_dataframe(self, limit: int = 1000) -> pd.DataFrame:
        """Retorna DataFrame de provisionamentos com informações unificadas"""
        provisionings_data = self.get_provisionings_with_users(limit)
        
        if not provisionings_data:
            return pd.DataFrame()
        
        # Processar dados para DataFrame
        processed_data = []
        
        for prov in provisionings_data:
            processed_data.append({
                'id': str(prov.get('_id')),
                'tipo': 'Grão' if prov.get('isGrain') else 'Frete' if prov.get('isFreight') else 'Outro',
                'grao': prov.get('grain', ''),
                'quantidade_total': prov.get('amount', 0),
                'quantidade_restante': prov.get('amountRemaining', 0),
                'quantidade_utilizada': (prov.get('amount', 0) - prov.get('amountRemaining', 0)),
                'preco_saca': prov.get('bagPrice', 0),
                'valor_total': prov.get('valor_total', 0),
                'valor_restante': prov.get('valor_restante', 0),
                'valor_utilizado': (prov.get('valor_total', 0) - prov.get('valor_restante', 0)),
                'percentual_utilizado': prov.get('percentual_utilizado', 0),
                'origem': prov.get('from_user_name', ''),
                'destino': prov.get('to_user_name', ''),
                'usuario': prov.get('user', ''),
                'fob': 'Sim' if prov.get('isFob') else 'Não',
                'preco_frete_total': prov.get('fullFreightPrice', 0),
                'prazo_entrega': prov.get('deliveryDeadline'),
                'dias_pagamento': prov.get('paymentDaysAfterDelivery', 0),
                'data_criacao': prov.get('createdAt'),
                'data_atualizacao': prov.get('updatedAt')
            })
        
        return pd.DataFrame(processed_data)
    
    def get_metricas_provisionamento(self) -> Dict[str, Any]:
        """Retorna métricas de provisionamento"""
        try:
            # Pipeline para métricas agregadas
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_provisionamentos": {"$sum": 1},
                        "total_quantidade": {"$sum": "$amount"},
                        "total_quantidade_restante": {"$sum": "$amountRemaining"},
                        "valor_total": {"$sum": {"$multiply": ["$amount", "$bagPrice"]}},
                        "valor_restante": {"$sum": {"$multiply": ["$amountRemaining", "$bagPrice"]}},
                        "preco_medio": {"$avg": "$bagPrice"},
                        "preco_minimo": {"$min": "$bagPrice"},
                        "preco_maximo": {"$max": "$bagPrice"},
                        "provisionamentos_grao": {
                            "$sum": {"$cond": [{"$eq": ["$isGrain", True]}, 1, 0]}
                        },
                        "provisionamentos_frete": {
                            "$sum": {"$cond": [{"$eq": ["$isFreight", True]}, 1, 0]}
                        }
                    }
                }
            ]
            
            result = list(self.provisionings.aggregate(pipeline))
            
            if result:
                metrics = result[0]
                
                # Calcular métricas derivadas
                total_qty = metrics.get('total_quantidade', 0)
                remaining_qty = metrics.get('total_quantidade_restante', 0)
                utilized_qty = total_qty - remaining_qty
                
                total_value = metrics.get('valor_total', 0)
                remaining_value = metrics.get('valor_restante', 0)
                utilized_value = total_value - remaining_value
                
                utilization_rate = (utilized_qty / total_qty * 100) if total_qty > 0 else 0
                
                return {
                    'total_provisionamentos': metrics.get('total_provisionamentos', 0),
                    'provisionamentos_grao': metrics.get('provisionamentos_grao', 0),
                    'provisionamentos_frete': metrics.get('provisionamentos_frete', 0),
                    'quantidade_total': total_qty,
                    'quantidade_restante': remaining_qty,
                    'quantidade_utilizada': utilized_qty,
                    'valor_total': total_value,
                    'valor_restante': remaining_value,
                    'valor_utilizado': utilized_value,
                    'preco_medio': metrics.get('preco_medio', 0),
                    'preco_minimo': metrics.get('preco_minimo', 0),
                    'preco_maximo': metrics.get('preco_maximo', 0),
                    'taxa_utilizacao': utilization_rate
                }
            
            return {}
            
        except Exception as e:
            print(f"Erro ao obter métricas de provisionamento: {e}")
            return {}
    
    def get_provisionamentos_por_usuario(self) -> pd.DataFrame:
        """Retorna provisionamentos agrupados por usuário"""
        pipeline = [
            {
                "$group": {
                    "_id": "$user",
                    "total_provisionamentos": {"$sum": 1},
                    "quantidade_total": {"$sum": "$amount"},
                    "quantidade_restante": {"$sum": "$amountRemaining"},
                    "valor_total": {"$sum": {"$multiply": ["$amount", "$bagPrice"]}},
                    "valor_restante": {"$sum": {"$multiply": ["$amountRemaining", "$bagPrice"]}},
                    "preco_medio": {"$avg": "$bagPrice"}
                }
            },
            {
                "$addFields": {
                    "quantidade_utilizada": {"$subtract": ["$quantidade_total", "$quantidade_restante"]},
                    "valor_utilizado": {"$subtract": ["$valor_total", "$valor_restante"]},
                    "taxa_utilizacao": {
                        "$cond": {
                            "if": {"$gt": ["$quantidade_total", 0]},
                            "then": {
                                "$multiply": [
                                    {"$divide": [
                                        {"$subtract": ["$quantidade_total", "$quantidade_restante"]},
                                        "$quantidade_total"
                                    ]},
                                    100
                                ]
                            },
                            "else": 0
                        }
                    }
                }
            },
            {"$sort": {"quantidade_total": -1}}
        ]
        
        try:
            results = list(self.provisionings.aggregate(pipeline))
            
            # Converter para DataFrame
            data = []
            for result in results:
                data.append({
                    'usuario': result.get('_id', 'Sem usuário'),
                    'total_provisionamentos': result.get('total_provisionamentos', 0),
                    'quantidade_total': result.get('quantidade_total', 0),
                    'quantidade_restante': result.get('quantidade_restante', 0),
                    'quantidade_utilizada': result.get('quantidade_utilizada', 0),
                    'valor_total': result.get('valor_total', 0),
                    'valor_restante': result.get('valor_restante', 0),
                    'valor_utilizado': result.get('valor_utilizado', 0),
                    'preco_medio': result.get('preco_medio', 0),
                    'taxa_utilizacao': result.get('taxa_utilizacao', 0)
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Erro ao agrupar por usuário: {e}")
            return pd.DataFrame()
    
    def get_alertas_provisionamento(self) -> Dict[str, List]:
        """Gera alertas para provisionamentos"""
        alertas = {
            'vencidos': [],
            'baixo_estoque': [],
            'sem_movimento': [],
            'preco_alto': []
        }
        
        try:
            # Buscar provisionamentos para análise
            provisionings = self.get_provisionings(limit=1000)
            
            if not provisionings:
                return alertas
            
            # Usar o processador para gerar alertas
            processor = ProvisioningProcessor()
            alertas = processor.get_alertas_provisionamento(provisionings)
            
            return alertas
            
        except Exception as e:
            print(f"Erro ao gerar alertas: {e}")
            return alertas

