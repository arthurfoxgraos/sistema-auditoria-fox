"""
Modelos de dados para o sistema de auditoria FOX
Baseado na estrutura real do MongoDB
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
    ticket: Optional[int]  # número do ticket
    status: str
    loadingDate: Optional[datetime]  # data de carregamento
    amount: Optional[float]  # quantidade de sacas (pode ser nan)
    destinationOrder: Optional[str]  # ID do pedido de destino
    originOrder: Optional[str]  # ID do pedido de origem
    seller: Optional[str]  # ID do vendedor
    buyer: Optional[str]  # ID do comprador
    responsible: Optional[str]  # ID do responsável
    freightValue: Optional[float]  # valor do frete
    valueGrain: Optional[float]  # valor do grão
    operation: Optional[str]  # ID da operação
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    
    @classmethod
    def from_mongo(cls, doc: Dict[str, Any]) -> 'Ticket':
        """Cria instância a partir de documento MongoDB"""
        # Tratar amount que pode ser nan
        amount = doc.get('amount')
        if amount is not None and (np.isnan(amount) if isinstance(amount, (int, float)) else False):
            amount = None
            
        return cls(
            _id=str(doc.get('_id', '')),
            ticket=doc.get('ticket'),
            status=doc.get('status', ''),
            loadingDate=doc.get('loadingDate'),
            amount=amount,
            destinationOrder=str(doc.get('destinationOrder', '')) if doc.get('destinationOrder') else None,
            originOrder=str(doc.get('originOrder', '')) if doc.get('originOrder') else None,
            seller=str(doc.get('seller', '')) if doc.get('seller') else None,
            buyer=str(doc.get('buyer', '')) if doc.get('buyer') else None,
            responsible=str(doc.get('responsible', '')) if doc.get('responsible') else None,
            freightValue=doc.get('freightValue'),
            valueGrain=doc.get('valueGrain'),
            operation=str(doc.get('operation', '')) if doc.get('operation') else None,
            createdAt=doc.get('createdAt'),
            updatedAt=doc.get('updatedAt')
        )

@dataclass
class TicketTransaction:
    """Modelo para transações de tickets (ticketv2_transactions)"""
    _id: str
    amount: Optional[int]  # quantidade de sacas
    destinationOrder: Optional[str]  # ID do pedido de destino
    originOrder: Optional[str]  # ID do pedido de origem
    ticket: Optional[str]  # ID do ticket
    status: str
    distanceInKm: Optional[float]  # distância em km
    value: Optional[float]  # valor
    total: Optional[float]  # total
    
    @classmethod
    def from_mongo(cls, doc: Dict[str, Any]) -> 'TicketTransaction':
        """Cria instância a partir de documento MongoDB"""
        return cls(
            _id=str(doc.get('_id', '')),
            amount=doc.get('amount'),
            destinationOrder=str(doc.get('destinationOrder', '')) if doc.get('destinationOrder') else None,
            originOrder=str(doc.get('originOrder', '')) if doc.get('originOrder') else None,
            ticket=str(doc.get('ticket', '')) if doc.get('ticket') else None,
            status=doc.get('status', ''),
            distanceInKm=doc.get('distanceInKm'),
            value=doc.get('value'),
            total=doc.get('total')
        )

@dataclass
class Order:
    """Modelo para pedidos (orderv2)"""
    _id: str
    buyer: Optional[Dict[str, Any]]  # informações do comprador
    seller: Optional[Dict[str, Any]]  # informações do vendedor
    amount: Optional[float]  # quantidade do pedido
    bagPrice: Optional[float]  # preço por saca
    deliveryDeadline: Optional[datetime]  # prazo de entrega
    status_flags: Dict[str, bool]  # isCanceled, isDone, isInProgress
    grain: Optional[str]  # ID do grão
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    operation: Optional[str]  # ID da operação
    
    @classmethod
    def from_mongo(cls, doc: Dict[str, Any]) -> 'Order':
        """Cria instância a partir de documento MongoDB"""
        return cls(
            _id=str(doc.get('_id', '')),
            buyer=doc.get('buyer'),
            seller=doc.get('seller'),
            amount=doc.get('amount'),
            bagPrice=doc.get('bagPrice'),
            deliveryDeadline=doc.get('deliveryDeadline'),
            status_flags={
                'isCanceled': doc.get('isCanceled', False),
                'isDone': doc.get('isDone', False),
                'isInProgress': doc.get('isInProgress', False)
            },
            grain=str(doc.get('grain', '')) if doc.get('grain') else None,
            createdAt=doc.get('createdAt'),
            updatedAt=doc.get('updatedAt'),
            operation=str(doc.get('operation', '')) if doc.get('operation') else None
        )

@dataclass
class Operacao:
    """Modelo para operações (conjunto de tickets)"""
    _id: str
    tickets: List[str]  # IDs dos tickets
    orders: List[str]  # IDs dos pedidos relacionados
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    status: str
    valor_total_frete: float
    valor_total_grao: float
    quantidade_total_sacas: int
    num_tickets: int
    
    @classmethod
    def from_tickets_and_orders(cls, tickets: List[Ticket], orders: List[Order]) -> 'Operacao':
        """Cria operação a partir de listas de tickets e pedidos"""
        if not tickets:
            raise ValueError("Lista de tickets não pode estar vazia")
        
        # Calcular valores totais
        valor_total_frete = sum(t.freightValue for t in tickets if t.freightValue)
        valor_total_grao = sum(t.valueGrain for t in tickets if t.valueGrain)
        quantidade_total_sacas = sum(t.amount for t in tickets if t.amount)
        
        # Determinar datas
        loading_dates = [t.loadingDate for t in tickets if t.loadingDate]
        data_inicio = min(loading_dates) if loading_dates else None
        data_fim = max(loading_dates) if loading_dates else None
        
        # Determinar status
        status = "ativa"
        if all(t.status == "Finalizado" for t in tickets):
            status = "finalizada"
        elif any(t.status == "Cancelado" for t in tickets):
            status = "com_problemas"
        
        return cls(
            _id=f"op_{len(tickets)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            tickets=[t._id for t in tickets],
            orders=[o._id for o in orders],
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status,
            valor_total_frete=valor_total_frete,
            valor_total_grao=valor_total_grao,
            quantidade_total_sacas=quantidade_total_sacas,
            num_tickets=len(tickets)
        )

class DataProcessor:
    """Processador de dados para análises"""
    
    @staticmethod
    def tickets_to_dataframe(tickets: List[Ticket]) -> pd.DataFrame:
        """Converte lista de tickets para DataFrame"""
        data = []
        for ticket in tickets:
            data.append({
                'id': ticket._id,
                'ticket_number': ticket.ticket,
                'status': ticket.status,
                'loadingDate': ticket.loadingDate,
                'amount': ticket.amount,
                'destinationOrder': ticket.destinationOrder,
                'originOrder': ticket.originOrder,
                'seller': ticket.seller,
                'buyer': ticket.buyer,
                'freightValue': ticket.freightValue,
                'valueGrain': ticket.valueGrain,
                'operation': ticket.operation,
                'createdAt': ticket.createdAt
            })
        
        df = pd.DataFrame(data)
        
        # Converter datas para datetime se necessário
        date_columns = ['loadingDate', 'createdAt']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    @staticmethod
    def ticket_transactions_to_dataframe(transactions: List[TicketTransaction]) -> pd.DataFrame:
        """Converte lista de transações para DataFrame"""
        data = []
        for trans in transactions:
            data.append({
                'id': trans._id,
                'amount': trans.amount,
                'destinationOrder': trans.destinationOrder,
                'originOrder': trans.originOrder,
                'ticket': trans.ticket,
                'status': trans.status,
                'distanceInKm': trans.distanceInKm,
                'value': trans.value,
                'total': trans.total
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def orders_to_dataframe(orders: List[Order]) -> pd.DataFrame:
        """Converte lista de pedidos para DataFrame"""
        data = []
        for order in orders:
            # Extrair informações do buyer e seller
            buyer_name = ""
            seller_name = ""
            
            if order.buyer and isinstance(order.buyer, dict):
                buyer_name = order.buyer.get('name', order.buyer.get('companyName', ''))
            elif order.buyer:
                # Se buyer for ObjectId ou string, converter para string
                buyer_name = str(order.buyer)
            
            if order.seller and isinstance(order.seller, dict):
                seller_name = order.seller.get('name', order.seller.get('companyName', ''))
            elif order.seller:
                # Se seller for ObjectId ou string, converter para string
                seller_name = str(order.seller)
            
            data.append({
                'id': order._id,
                'buyer_name': buyer_name,
                'seller_name': seller_name,
                'amount': order.amount,
                'bagPrice': order.bagPrice,
                'deliveryDeadline': order.deliveryDeadline,
                'isCanceled': order.status_flags['isCanceled'],
                'isDone': order.status_flags['isDone'],
                'isInProgress': order.status_flags['isInProgress'],
                'grain': order.grain,
                'operation': order.operation,
                'createdAt': order.createdAt
            })
        
        df = pd.DataFrame(data)
        
        # Converter datas
        date_columns = ['deliveryDeadline', 'createdAt']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    @staticmethod
    def calcular_metricas_gerais(tickets: List[Ticket], orders: List[Order]) -> Dict[str, Any]:
        """Calcula métricas gerais do sistema"""
        # Métricas de tickets
        total_tickets = len(tickets)
        tickets_finalizados = len([t for t in tickets if t.status == "Finalizado"])
        tickets_com_amount = len([t for t in tickets if t.amount is not None])
        
        # Valores totais
        total_frete = sum(t.freightValue for t in tickets if t.freightValue)
        total_grao = sum(t.valueGrain for t in tickets if t.valueGrain)
        total_sacas = sum(t.amount for t in tickets if t.amount)
        
        # Métricas de pedidos
        total_orders = len(orders)
        orders_done = len([o for o in orders if o.status_flags['isDone']])
        orders_canceled = len([o for o in orders if o.status_flags['isCanceled']])
        
        return {
            'total_tickets': total_tickets,
            'tickets_finalizados': tickets_finalizados,
            'taxa_finalizacao': tickets_finalizados / total_tickets if total_tickets > 0 else 0,
            'tickets_com_amount': tickets_com_amount,
            'taxa_amount_preenchido': tickets_com_amount / total_tickets if total_tickets > 0 else 0,
            'total_valor_frete': total_frete,
            'total_valor_grao': total_grao,
            'total_sacas': total_sacas,
            'valor_medio_frete': total_frete / total_tickets if total_tickets > 0 else 0,
            'sacas_media_ticket': total_sacas / tickets_com_amount if tickets_com_amount > 0 else 0,
            'total_orders': total_orders,
            'orders_done': orders_done,
            'orders_canceled': orders_canceled,
            'taxa_orders_done': orders_done / total_orders if total_orders > 0 else 0
        }

