"""
Serviço de acesso ao banco de dados com lookup de users
"""
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from bson import ObjectId

from .data_models import Ticket, TicketTransaction, Order

class DatabaseService:
    """Serviço para acesso aos dados do MongoDB"""
    
    def __init__(self, collections):
        self.ticketv2 = collections['ticketv2']
        self.ticketv2_transactions = collections['ticketv2_transactions']
        self.orderv2 = collections['orderv2']
        self.users = collections['users']
        self.provisionings = collections['provisionings']
    
    def get_tickets_with_users(self, limit: int = 100) -> List[Dict]:
        """Busca tickets com lookup de users para seller e buyer"""
        pipeline = [
            # Lookup com orderv2 para destinationOrder
            {
                "$lookup": {
                    "from": "orderv2",
                    "localField": "destinationOrder",
                    "foreignField": "_id",
                    "as": "destination_order_info"
                }
            },
            # Lookup com orderv2 para originOrder
            {
                "$lookup": {
                    "from": "orderv2",
                    "localField": "originOrder", 
                    "foreignField": "_id",
                    "as": "origin_order_info"
                }
            },
            # Lookup com users para buyer (via destination order)
            {
                "$lookup": {
                    "from": "users",
                    "localField": "destination_order_info.buyer",
                    "foreignField": "_id",
                    "as": "buyer_info"
                }
            },
            # Lookup com users para seller (via origin order)
            {
                "$lookup": {
                    "from": "users",
                    "localField": "origin_order_info.seller",
                    "foreignField": "_id", 
                    "as": "seller_info"
                }
            },
            # Lookup com transações
            {
                "$lookup": {
                    "from": "ticketv2_transactions",
                    "localField": "_id",
                    "foreignField": "ticket",
                    "as": "transactions"
                }
            },
            # Adicionar campos calculados
            {
                "$addFields": {
                    "buyer_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$buyer_info.name", 0]},
                            {"$arrayElemAt": ["$buyer_info.companyName", 0]}
                        ]
                    },
                    "seller_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$seller_info.name", 0]},
                            {"$arrayElemAt": ["$seller_info.companyName", 0]}
                        ]
                    },
                    "transaction_amount": {
                        "$sum": "$transactions.amount"
                    },
                    "transaction_distance": {
                        "$avg": "$transactions.distanceInKm"
                    },
                    "transaction_value": {
                        "$sum": "$transactions.value"
                    }
                }
            },
            {"$limit": limit}
        ]
        
        try:
            results = list(self.ticketv2.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Erro ao buscar tickets com users: {e}")
            return []
    
    def get_tickets(self, limit: int = 100) -> List[Ticket]:
        """Busca tickets básicos"""
        try:
            cursor = self.ticketv2.find().limit(limit)
            tickets = []
            
            for doc in cursor:
                ticket = Ticket(
                    _id=str(doc.get('_id')),
                    ticket=doc.get('ticket', 0),
                    status=doc.get('status'),
                    loadingDate=doc.get('loadingDate'),
                    amount=doc.get('amount'),
                    destinationOrder=str(doc.get('destinationOrder')) if doc.get('destinationOrder') else None,
                    originOrder=str(doc.get('originOrder')) if doc.get('originOrder') else None,
                    seller=doc.get('seller'),
                    buyer=doc.get('buyer'),
                    freightValue=doc.get('freightValue'),
                    valueGrain=doc.get('valueGrain'),
                    operation=str(doc.get('operation')) if doc.get('operation') else None,
                    createdAt=doc.get('createdAt')
                )
                tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            print(f"Erro ao buscar tickets: {e}")
            return []
    
    def get_ticket_transactions(self, limit: int = 100) -> List[TicketTransaction]:
        """Busca transações de tickets"""
        try:
            cursor = self.ticketv2_transactions.find().limit(limit)
            transactions = []
            
            for doc in cursor:
                transaction = TicketTransaction(
                    _id=str(doc.get('_id')),
                    amount=doc.get('amount'),
                    destinationOrder=str(doc.get('destinationOrder')) if doc.get('destinationOrder') else None,
                    originOrder=str(doc.get('originOrder')) if doc.get('originOrder') else None,
                    ticket=str(doc.get('ticket')) if doc.get('ticket') else None,
                    status=doc.get('status'),
                    distanceInKm=doc.get('distanceInKm'),
                    value=doc.get('value'),
                    total=doc.get('total')
                )
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            print(f"Erro ao buscar transações: {e}")
            return []
    
    def get_orders(self, limit: int = 100) -> List[Order]:
        """Busca pedidos/contratos"""
        try:
            cursor = self.orderv2.find().limit(limit)
            orders = []
            
            for doc in cursor:
                order = Order(
                    _id=str(doc.get('_id')),
                    amount=doc.get('amount'),
                    bagPrice=doc.get('bagPrice'),
                    deliveryDeadline=doc.get('deliveryDeadline'),
                    buyer=doc.get('buyer'),
                    seller=doc.get('seller'),
                    status_flags={
                        'isDone': doc.get('isDone', False),
                        'isCanceled': doc.get('isCanceled', False),
                        'isInProgress': doc.get('isInProgress', False)
                    },
                    createdAt=doc.get('createdAt')
                )
                orders.append(order)
            
            return orders
            
        except Exception as e:
            print(f"Erro ao buscar pedidos: {e}")
            return []
    
    def get_users(self, limit: int = 100) -> List[Dict]:
        """Busca usuários"""
        try:
            cursor = self.users.find().limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"Erro ao buscar usuários: {e}")
            return []
    
    def get_cargas_dataframe(self, limit: int = 1000) -> pd.DataFrame:
        """Retorna DataFrame de cargas com informações unificadas"""
        cargas_data = self.get_tickets_with_users(limit)
        
        if not cargas_data:
            return pd.DataFrame()
        
        # Processar dados para DataFrame
        processed_data = []
        
        for carga in cargas_data:
            processed_data.append({
                'id': str(carga.get('_id')),
                'numero_carga': carga.get('ticket', 0),
                'status': carga.get('status', ''),
                'data_carregamento': carga.get('loadingDate'),
                'quantidade_sacas': carga.get('amount', 0),
                'valor_frete': carga.get('freightValue', 0),
                'valor_grao': carga.get('valueGrain', 0),
                'comprador': carga.get('buyer_name', ''),
                'vendedor': carga.get('seller_name', ''),
                'quantidade_transacao': carga.get('transaction_amount', 0),
                'distancia_km': carga.get('transaction_distance', 0),
                'valor_transacao': carga.get('transaction_value', 0),
                'operacao': carga.get('operation', ''),
                'data_criacao': carga.get('createdAt')
            })
        
        return pd.DataFrame(processed_data)
    
    def get_operation_statistics(self) -> pd.DataFrame:
        """Retorna estatísticas por operação"""
        pipeline = [
            {"$match": {"operation": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": "$operation",
                    "total_tickets": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "total_freight_value": {"$sum": "$freightValue"},
                    "total_grain_value": {"$sum": "$valueGrain"},
                    "avg_freight_value": {"$avg": "$freightValue"}
                }
            },
            {"$sort": {"total_tickets": -1}}
        ]
        
        try:
            results = list(self.ticketv2.aggregate(pipeline))
            return pd.DataFrame(results)
        except Exception as e:
            print(f"Erro ao obter estatísticas de operação: {e}")
            return pd.DataFrame()
    
    def get_daily_statistics(self, days: int = 30) -> pd.DataFrame:
        """Retorna estatísticas diárias"""
        start_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"loadingDate": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$loadingDate"
                        }
                    },
                    "total_tickets": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "total_freight_value": {"$sum": "$freightValue"},
                    "avg_freight_value": {"$avg": "$freightValue"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        try:
            results = list(self.ticketv2.aggregate(pipeline))
            return pd.DataFrame(results)
        except Exception as e:
            print(f"Erro ao obter estatísticas diárias: {e}")
            return pd.DataFrame()
    
    def get_orders_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos pedidos/contratos"""
        try:
            total_orders = self.orderv2.count_documents({})
            
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_amount": {"$sum": "$amount"},
                        "media_amount": {"$avg": "$amount"},
                        "total_bag_price": {"$sum": "$bagPrice"},
                        "media_bag_price": {"$avg": "$bagPrice"},
                        "done_count": {
                            "$sum": {"$cond": [{"$eq": ["$isDone", True]}, 1, 0]}
                        },
                        "canceled_count": {
                            "$sum": {"$cond": [{"$eq": ["$isCanceled", True]}, 1, 0]}
                        }
                    }
                }
            ]
            
            result = list(self.orderv2.aggregate(pipeline))
            
            if result:
                summary = result[0]
                summary['total_orders'] = total_orders
                summary['done_rate'] = summary['done_count'] / total_orders if total_orders > 0 else 0
                return summary
            
            return {'total_orders': total_orders}
            
        except Exception as e:
            print(f"Erro ao obter resumo de pedidos: {e}")
            return {}
    
    def get_audit_alerts(self) -> Dict[str, List]:
        """Retorna alertas de auditoria"""
        alerts = {
            'cargas_sem_amount': [],
            'cargas_sem_orders': [],
            'cargas_com_problemas': [],
            'contratos_vencidos': []
        }
        
        try:
            # Cargas sem quantidade
            cargas_sem_amount = self.ticketv2.find(
                {"amount": {"$in": [None, 0]}},
                {"_id": 1, "ticket": 1, "status": 1, "loadingDate": 1}
            ).limit(10)
            
            for carga in cargas_sem_amount:
                alerts['cargas_sem_amount'].append({
                    'carga_id': str(carga['_id']),
                    'numero_carga': carga.get('ticket', 0),
                    'status': carga.get('status'),
                    'loadingDate': carga.get('loadingDate')
                })
            
            # Cargas sem pedidos
            cargas_sem_orders = self.ticketv2.find(
                {
                    "$and": [
                        {"destinationOrder": {"$in": [None, ""]}},
                        {"originOrder": {"$in": [None, ""]}}
                    ]
                },
                {"_id": 1, "ticket": 1, "status": 1, "loadingDate": 1}
            ).limit(10)
            
            for carga in cargas_sem_orders:
                alerts['cargas_sem_orders'].append({
                    'carga_id': str(carga['_id']),
                    'numero_carga': carga.get('ticket', 0),
                    'status': carga.get('status'),
                    'loadingDate': carga.get('loadingDate')
                })
            
            return alerts
            
        except Exception as e:
            print(f"Erro ao obter alertas: {e}")
            return alerts

