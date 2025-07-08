"""
Serviço de acesso ao banco de dados - Versão atualizada com driver
"""
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from bson import ObjectId

from .data_models import Ticket, TicketTransaction, Order, DataProcessor

class DatabaseService:
    """Serviço para acesso aos dados do MongoDB"""
    
    def __init__(self, collections):
        self.ticketv2 = collections['ticketv2']
        self.ticketv2_transactions = collections['ticketv2_transactions']
        self.orderv2 = collections['orderv2']
        self.users = collections['users']
        self.provisionings = collections['provisionings']
    
    def get_tickets_with_users(self, limit: int = 100) -> List[Dict]:
        """Busca tickets com lookup de users para seller, buyer e driver"""
        pipeline = [
            # Filtrar apenas cargas a partir de 2025
            {
                "$match": {
                    "loadingDate": {
                        "$gte": datetime(2025, 1, 1)
                    }
                }
            },
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
            # Lookup com users para buyer (do destinationOrder)
            {
                "$lookup": {
                    "from": "users",
                    "localField": "destination_order_info.buyer",
                    "foreignField": "_id",
                    "as": "buyer_info"
                }
            },
            # Lookup com users para seller (do originOrder)
            {
                "$lookup": {
                    "from": "users",
                    "localField": "origin_order_info.seller",
                    "foreignField": "_id",
                    "as": "seller_info"
                }
            },
            # Lookup com users para driver
            {
                "$lookup": {
                    "from": "users",
                    "localField": "userDriver",
                    "foreignField": "_id",
                    "as": "driver_info"
                }
            },
            # Lookup com grains através do destinationOrder
            {
                "$lookup": {
                    "from": "grains",
                    "localField": "destination_order_info.grain",
                    "foreignField": "_id",
                    "as": "grain_info"
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
                    "driver_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$driver_info.name", 0]},
                            "$driverName"
                        ]
                    },
                    "grain_name": {"$arrayElemAt": ["$grain_info.name", 0]},
                    # Extrair amount do array transactions
                    "amount": {"$sum": "$transactions.amount"},
                    "transaction_distance": {"$avg": "$transactions.distanceInKm"},
                    "transaction_value": {"$sum": "$transactions.valueGrainReceive"}
                }
            },
            # Lookup com provisionamentos para verificar conformidade
            {
                "$lookup": {
                    "from": "provisionings",
                    "let": {
                        "dest_order": "$destinationOrder",
                        "orig_order": "$originOrder"
                    },
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$or": [
                                        {"$eq": ["$_id", "$$dest_order"]},
                                        {"$in": ["$$orig_order", "$sellersOrders._id"]}
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "matching_provisionings"
                }
            },
            # Adicionar status de conformidade
            {
                "$addFields": {
                    "is_compliant": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$matching_provisionings"}, 0]},
                            "then": True,
                            "else": False
                        }
                    },
                    "compliance_status": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$matching_provisionings"}, 0]},
                            "then": "✅ Conforme",
                            "else": "⚠️ Não conforme"
                        }
                    }
                }
            },
            {"$sort": {"ticket": -1}},
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
            cursor = self.ticketv2.find().limit(limit).sort("loadingDate", -1)
            tickets = []
            
            for doc in cursor:
                ticket = Ticket(
                    _id=str(doc.get('_id')),
                    ticket=doc.get('ticket'),
                    status=doc.get('status'),
                    loadingDate=doc.get('loadingDate'),
                    amount=doc.get('amount'),
                    destinationOrder=str(doc.get('destinationOrder')) if doc.get('destinationOrder') else None,
                    originOrder=str(doc.get('originOrder')) if doc.get('originOrder') else None,
                    seller=str(doc.get('seller')) if doc.get('seller') else None,
                    buyer=str(doc.get('buyer')) if doc.get('buyer') else None,
                    responsible=str(doc.get('responsible')) if doc.get('responsible') else None,
                    freightValue=doc.get('freightValue'),
                    valueGrain=doc.get('valueGrain'),
                    operation=str(doc.get('operation')) if doc.get('operation') else None,
                    createdAt=doc.get('createdAt'),
                    updatedAt=doc.get('updatedAt')
                )
                tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            print(f"Erro ao buscar tickets: {e}")
            return []
    
    def get_orders(self, limit: int = 100) -> List[Order]:
        """Busca pedidos/contratos"""
        try:
            cursor = self.orderv2.find().limit(limit).sort("createdAt", -1)
            orders = []
            
            for doc in cursor:
                # Extrair flags de status
                status_flags = {}
                for flag in ['isDone', 'isCanceled', 'isInProgress']:
                    status_flags[flag] = doc.get(flag, False)
                
                order = Order(
                    _id=str(doc.get('_id')),
                    amount=doc.get('amount'),
                    bagPrice=doc.get('bagPrice'),
                    deliveryDeadline=doc.get('deliveryDeadline'),
                    buyer=str(doc.get('buyer')) if doc.get('buyer') else None,
                    seller=str(doc.get('seller')) if doc.get('seller') else None,
                    status_flags=status_flags,
                    createdAt=doc.get('createdAt'),
                    grain=doc.get('grain'),
                    updatedAt=doc.get('updatedAt'),
                    operation=str(doc.get('operation')) if doc.get('operation') else None
                )
                orders.append(order)
            
            return orders
            
        except Exception as e:
            print(f"Erro ao buscar pedidos: {e}")
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

