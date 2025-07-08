"""
Modelos de dados para o sistema de auditoria FOX - Versão corrigida
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

@dataclass
class Ticket:
    """Modelo para tickets de carga (ticketv2)"""
    _id: str
    ticket: Optional[int] = None
    status: Optional[str] = None
    loadingDate: Optional[datetime] = None
    amount: Optional[float] = None
    destinationOrder: Optional[str] = None
    originOrder: Optional[str] = None
    seller: Optional[str] = None
    buyer: Optional[str] = None
    responsible: Optional[str] = None
    freightValue: Optional[float] = None
    valueGrain: Optional[float] = None
    operation: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

@dataclass
class TicketTransaction:
    """Modelo para transações de tickets"""
    _id: str
    amount: Optional[float] = None
    destinationOrder: Optional[str] = None
    originOrder: Optional[str] = None
    ticket: Optional[str] = None
    status: Optional[str] = None
    distanceInKm: Optional[float] = None
    value: Optional[float] = None
    total: Optional[float] = None

@dataclass
class Order:
    """Modelo para pedidos/contratos (orderv2)"""
    _id: str
    amount: Optional[float] = None
    bagPrice: Optional[float] = None
    deliveryDeadline: Optional[datetime] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    status_flags: Optional[Dict[str, bool]] = None
    createdAt: Optional[datetime] = None
    grain: Optional[str] = None
    updatedAt: Optional[datetime] = None
    operation: Optional[str] = None

@dataclass
class Operation:
    """Modelo para operações"""
    _id: str
    tickets: List[str]
    status: str
    data_inicio: datetime
    data_fim: Optional[datetime]
    num_tickets: int
    quantidade_total_sacas: float
    valor_total_frete: float
    valor_total_grao: float

class DataProcessor:
    """Processador de dados para conversões e análises"""
    
    @staticmethod
    def tickets_to_dataframe(tickets: List[Ticket]) -> pd.DataFrame:
        """Converte lista de tickets para DataFrame"""
        data = []
        for ticket in tickets:
            data.append({
                'id': ticket._id,
                'numero_ticket': ticket.ticket,
                'status': ticket.status,
                'data_carregamento': ticket.loadingDate,
                'quantidade': ticket.amount,
                'valor_frete': ticket.freightValue,
                'valor_grao': ticket.valueGrain,
                'pedido_destino': ticket.destinationOrder,
                'pedido_origem': ticket.originOrder,
                'vendedor': ticket.seller,
                'comprador': ticket.buyer,
                'responsavel': ticket.responsible,
                'operacao': ticket.operation,
                'data_criacao': ticket.createdAt,
                'data_atualizacao': ticket.updatedAt
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def orders_to_dataframe(orders: List[Order]) -> pd.DataFrame:
        """Converte lista de pedidos para DataFrame"""
        data = []
        for order in orders:
            # Extrair flags de status
            is_done = False
            is_canceled = False
            is_in_progress = False
            
            if order.status_flags:
                is_done = order.status_flags.get('isDone', False)
                is_canceled = order.status_flags.get('isCanceled', False)
                is_in_progress = order.status_flags.get('isInProgress', False)
            
            data.append({
                'id': order._id,
                'quantidade': order.amount,
                'preco_saca': order.bagPrice,
                'prazo_entrega': order.deliveryDeadline,
                'comprador': order.buyer,
                'vendedor': order.seller,
                'grao': order.grain,
                'isDone': is_done,
                'isCanceled': is_canceled,
                'isInProgress': is_in_progress,
                'operacao': order.operation,
                'data_criacao': order.createdAt,
                'data_atualizacao': order.updatedAt
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def transactions_to_dataframe(transactions: List[TicketTransaction]) -> pd.DataFrame:
        """Converte lista de transações para DataFrame"""
        data = []
        for trans in transactions:
            data.append({
                'id': trans._id,
                'quantidade': trans.amount,
                'ticket': trans.ticket,
                'pedido_destino': trans.destinationOrder,
                'pedido_origem': trans.originOrder,
                'status': trans.status,
                'distancia_km': trans.distanceInKm,
                'valor': trans.value,
                'total': trans.total
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def calcular_metricas_gerais(tickets: List[Ticket], orders: List[Order]) -> Dict[str, float]:
        """Calcula métricas gerais do sistema"""
        # Métricas de tickets
        total_tickets = len(tickets)
        tickets_finalizados = len([t for t in tickets if t.status == 'Finalizado'])
        taxa_finalizacao = tickets_finalizados / total_tickets if total_tickets > 0 else 0
        
        # Tickets com amount preenchido
        tickets_com_amount = len([t for t in tickets if t.amount is not None])
        taxa_amount_preenchido = tickets_com_amount / total_tickets if total_tickets > 0 else 0
        
        # Valores médios
        valores_frete = [t.freightValue for t in tickets if t.freightValue is not None]
        valor_medio_frete = sum(valores_frete) / len(valores_frete) if valores_frete else 0
        
        amounts = [t.amount for t in tickets if t.amount is not None]
        sacas_media_ticket = sum(amounts) / len(amounts) if amounts else 0
        total_sacas = sum(amounts) if amounts else 0
        
        # Métricas de orders
        total_orders = len(orders)
        orders_done = len([o for o in orders if o.status_flags and o.status_flags.get('isDone', False)])
        taxa_orders_done = orders_done / total_orders if total_orders > 0 else 0
        
        return {
            'total_tickets': total_tickets,
            'tickets_finalizados': tickets_finalizados,
            'taxa_finalizacao': taxa_finalizacao,
            'taxa_amount_preenchido': taxa_amount_preenchido,
            'valor_medio_frete': valor_medio_frete,
            'sacas_media_ticket': sacas_media_ticket,
            'total_sacas': total_sacas,
            'total_orders': total_orders,
            'orders_done': orders_done,
            'taxa_orders_done': taxa_orders_done
        }

