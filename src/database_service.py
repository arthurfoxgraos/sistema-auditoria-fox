"""
Serviço de acesso ao banco de dados MongoDB para auditoria FOX
Baseado na estrutura real das coleções
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING

from .data_models import Ticket, TicketTransaction, Order, Operacao

class DatabaseService:
    """Serviço para operações no banco de dados"""
    
    def __init__(self, collections: Dict[str, Collection]):
        self.ticketv2 = collections['ticketv2']
        self.ticketv2_transactions = collections['ticketv2_transactions']
        self.orderv2 = collections['orderv2']
    
    def get_tickets(self, limit: int = 1000, filters: Dict = None) -> List[Ticket]:
        """Busca tickets da coleção ticketv2"""
        query = filters or {}
        
        tickets = []
        for doc in self.ticketv2.find(query).limit(limit).sort("loadingDate", DESCENDING):
            try:
                ticket = Ticket.from_mongo(doc)
                tickets.append(ticket)
            except Exception as e:
                print(f"Erro ao processar ticket {doc.get('_id')}: {e}")
                continue
        
        return tickets
    
    def get_ticket_transactions(self, limit: int = 1000, filters: Dict = None) -> List[TicketTransaction]:
        """Busca transações da coleção ticketv2_transactions"""
        query = filters or {}
        
        transactions = []
        for doc in self.ticketv2_transactions.find(query).limit(limit):
            try:
                transaction = TicketTransaction.from_mongo(doc)
                transactions.append(transaction)
            except Exception as e:
                print(f"Erro ao processar transação {doc.get('_id')}: {e}")
                continue
        
        return transactions
    
    def get_orders(self, limit: int = 1000, filters: Dict = None) -> List[Order]:
        """Busca pedidos da coleção orderv2"""
        query = filters or {}
        
        orders = []
        for doc in self.orderv2.find(query).limit(limit).sort("createdAt", DESCENDING):
            try:
                order = Order.from_mongo(doc)
                orders.append(order)
            except Exception as e:
                print(f"Erro ao processar pedido {doc.get('_id')}: {e}")
                continue
        
        return orders
    
    def get_tickets_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Ticket]:
        """Busca tickets por período de data de carregamento"""
        filters = {
            "loadingDate": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        return self.get_tickets(filters=filters)
    
    def get_tickets_by_status(self, status: str) -> List[Ticket]:
        """Busca tickets por status específico"""
        filters = {"status": status}
        return self.get_tickets(filters=filters)
    
    def get_tickets_with_orders(self) -> List[Dict[str, Any]]:
        """Busca tickets com informações dos pedidos relacionados (lookup)"""
        pipeline = [
            # Lookup para destinationOrder
            {
                "$lookup": {
                    "from": "orderv2",
                    "localField": "destinationOrder",
                    "foreignField": "_id",
                    "as": "destination_order_info"
                }
            },
            # Lookup para originOrder
            {
                "$lookup": {
                    "from": "orderv2",
                    "localField": "originOrder",
                    "foreignField": "_id",
                    "as": "origin_order_info"
                }
            },
            # Limitar resultados
            {"$limit": 1000},
            # Ordenar por data de carregamento
            {"$sort": {"loadingDate": DESCENDING}}
        ]
        
        results = []
        for doc in self.ticketv2.aggregate(pipeline):
            try:
                # Processar ticket
                ticket = Ticket.from_mongo(doc)
                
                # Processar pedidos relacionados
                destination_orders = []
                origin_orders = []
                
                for order_doc in doc.get('destination_order_info', []):
                    destination_orders.append(Order.from_mongo(order_doc))
                
                for order_doc in doc.get('origin_order_info', []):
                    origin_orders.append(Order.from_mongo(order_doc))
                
                results.append({
                    'ticket': ticket,
                    'destination_orders': destination_orders,
                    'origin_orders': origin_orders
                })
                
            except Exception as e:
                print(f"Erro ao processar ticket com lookup {doc.get('_id')}: {e}")
                continue
        
        return results
    
    def get_orders_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos pedidos (orderv2)"""
        total_orders = self.orderv2.count_documents({})
        
        # Agregação para estatísticas
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$amount"},
                    "media_amount": {"$avg": "$amount"},
                    "total_bag_price": {"$sum": "$bagPrice"},
                    "media_bag_price": {"$avg": "$bagPrice"},
                    "count": {"$sum": 1},
                    "done_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$isDone", True]}, 1, 0]
                        }
                    },
                    "canceled_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$isCanceled", True]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        stats = list(self.orderv2.aggregate(pipeline))
        
        if stats:
            stat = stats[0]
            return {
                "total_orders": total_orders,
                "total_amount": stat.get("total_amount", 0),
                "media_amount": stat.get("media_amount", 0),
                "total_bag_price": stat.get("total_bag_price", 0),
                "media_bag_price": stat.get("media_bag_price", 0),
                "done_count": stat.get("done_count", 0),
                "canceled_count": stat.get("canceled_count", 0),
                "done_rate": stat.get("done_count", 0) / total_orders if total_orders > 0 else 0
            }
        else:
            return {
                "total_orders": total_orders,
                "total_amount": 0,
                "media_amount": 0,
                "total_bag_price": 0,
                "media_bag_price": 0,
                "done_count": 0,
                "canceled_count": 0,
                "done_rate": 0
            }
    
    def get_tickets_without_amount(self) -> List[Ticket]:
        """Busca tickets sem quantidade (amount) definida"""
        filters = {
            "$or": [
                {"amount": {"$exists": False}},
                {"amount": None},
                {"amount": {"$in": [float('nan'), "nan"]}}
            ]
        }
        
        return self.get_tickets(filters=filters)
    
    def get_tickets_without_orders(self) -> List[Ticket]:
        """Busca tickets sem pedidos associados"""
        filters = {
            "$and": [
                {
                    "$or": [
                        {"destinationOrder": {"$exists": False}},
                        {"destinationOrder": None}
                    ]
                },
                {
                    "$or": [
                        {"originOrder": {"$exists": False}},
                        {"originOrder": None}
                    ]
                }
            ]
        }
        
        return self.get_tickets(filters=filters)
    
    def get_operation_statistics(self) -> pd.DataFrame:
        """Retorna estatísticas por operação"""
        pipeline = [
            {
                "$match": {
                    "operation": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$operation",
                    "total_tickets": {"$sum": 1},
                    "total_freight_value": {"$sum": "$freightValue"},
                    "total_grain_value": {"$sum": "$valueGrain"},
                    "total_amount": {"$sum": "$amount"},
                    "avg_freight_value": {"$avg": "$freightValue"},
                    "avg_grain_value": {"$avg": "$valueGrain"},
                    "avg_amount": {"$avg": "$amount"},
                    "statuses": {"$addToSet": "$status"}
                }
            },
            {
                "$sort": {"total_tickets": DESCENDING}
            }
        ]
        
        operation_stats = list(self.ticketv2.aggregate(pipeline))
        
        # Converter para DataFrame
        data = []
        for stat in operation_stats:
            data.append({
                'operation_id': str(stat['_id']),
                'total_tickets': stat['total_tickets'],
                'total_freight_value': stat.get('total_freight_value', 0),
                'total_grain_value': stat.get('total_grain_value', 0),
                'total_amount': stat.get('total_amount', 0),
                'avg_freight_value': stat.get('avg_freight_value', 0),
                'avg_grain_value': stat.get('avg_grain_value', 0),
                'avg_amount': stat.get('avg_amount', 0),
                'statuses': ', '.join(stat.get('statuses', []))
            })
        
        return pd.DataFrame(data)
    
    def get_daily_statistics(self, days: int = 30) -> pd.DataFrame:
        """Retorna estatísticas diárias dos últimos N dias"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "loadingDate": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$loadingDate"
                        }
                    },
                    "total_tickets": {"$sum": 1},
                    "total_freight_value": {"$sum": "$freightValue"},
                    "total_grain_value": {"$sum": "$valueGrain"},
                    "total_amount": {"$sum": "$amount"}
                }
            },
            {
                "$sort": {"_id": ASCENDING}
            }
        ]
        
        daily_stats = list(self.ticketv2.aggregate(pipeline))
        
        # Converter para DataFrame
        data = []
        for stat in daily_stats:
            data.append({
                'data': stat['_id'],
                'total_tickets': stat['total_tickets'],
                'total_freight_value': stat.get('total_freight_value', 0),
                'total_grain_value': stat.get('total_grain_value', 0),
                'total_amount': stat.get('total_amount', 0)
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
        
        return df
    
    def search_tickets(self, search_term: str) -> List[Ticket]:
        """Busca tickets por termo (número, status, etc.)"""
        # Tentar converter para número se possível
        try:
            ticket_number = int(search_term)
            filters = {"ticket": ticket_number}
        except ValueError:
            # Busca por texto
            filters = {
                "$or": [
                    {"status": {"$regex": search_term, "$options": "i"}},
                    {"_id": {"$regex": search_term, "$options": "i"}}
                ]
            }
        
        return self.get_tickets(filters=filters)
    
    def get_audit_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna alertas de auditoria"""
        alerts = {
            'tickets_sem_amount': [],
            'tickets_sem_orders': [],
            'tickets_com_problemas': [],
            'orders_vencidos': []
        }
        
        # Tickets sem amount
        tickets_sem_amount = self.get_tickets_without_amount()
        for ticket in tickets_sem_amount[:10]:  # Limitar a 10
            alerts['tickets_sem_amount'].append({
                'ticket_id': ticket._id,
                'ticket_number': ticket.ticket,
                'status': ticket.status,
                'loadingDate': ticket.loadingDate
            })
        
        # Tickets sem pedidos
        tickets_sem_orders = self.get_tickets_without_orders()
        for ticket in tickets_sem_orders[:10]:  # Limitar a 10
            alerts['tickets_sem_orders'].append({
                'ticket_id': ticket._id,
                'ticket_number': ticket.ticket,
                'status': ticket.status,
                'loadingDate': ticket.loadingDate
            })
        
        # Orders vencidos (prazo de entrega passou)
        today = datetime.now()
        filters = {
            "deliveryDeadline": {"$lt": today},
            "isDone": False,
            "isCanceled": False
        }
        
        for doc in self.orderv2.find(filters).limit(10):
            try:
                order = Order.from_mongo(doc)
                alerts['orders_vencidos'].append({
                    'order_id': order._id,
                    'deliveryDeadline': order.deliveryDeadline,
                    'amount': order.amount,
                    'buyer_name': order.buyer.get('name', '') if order.buyer else '',
                    'seller_name': order.seller.get('name', '') if order.seller else ''
                })
            except Exception as e:
                continue
        
        return alerts

