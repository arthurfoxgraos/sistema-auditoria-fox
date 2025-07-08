"""
Modelos de dados para provisionamento
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd

@dataclass
class Provisioning:
    """Modelo para provisionamento"""
    _id: str
    amount: Optional[float] = None
    amountRemaining: Optional[float] = None
    bagPrice: Optional[float] = None
    createdAt: Optional[datetime] = None
    deliveryDeadline: Optional[datetime] = None
    deliveryDeadlineEnd: Optional[datetime] = None
    from_location: Optional[str] = None  # from é palavra reservada
    to_location: Optional[str] = None    # to é palavra reservada
    fullFreightPrice: Optional[float] = None
    grain: Optional[str] = None
    isFob: Optional[bool] = None
    isFreight: Optional[bool] = None
    isGrain: Optional[bool] = None
    paymentDaysAfterDelivery: Optional[int] = None
    sellersOrders: Optional[List] = None
    updatedAt: Optional[datetime] = None
    user: Optional[str] = None
    order: Optional[str] = None
    pisCofins: Optional[float] = None
    promotor: Optional[str] = None

class ProvisioningProcessor:
    """Processador de dados de provisionamento"""
    
    @staticmethod
    def to_dataframe(provisionings: List[Provisioning]) -> pd.DataFrame:
        """Converte lista de provisionamentos para DataFrame"""
        data = []
        
        for prov in provisionings:
            data.append({
                'id': prov._id,
                'quantidade': prov.amount,
                'quantidade_restante': prov.amountRemaining,
                'preco_saca': prov.bagPrice,
                'valor_total': (prov.amount * prov.bagPrice) if (prov.amount and prov.bagPrice) else 0,
                'valor_restante': (prov.amountRemaining * prov.bagPrice) if (prov.amountRemaining and prov.bagPrice) else 0,
                'tipo_grao': prov.isGrain,
                'tipo_frete': prov.isFreight,
                'fob': prov.isFob,
                'origem': prov.from_location,
                'destino': prov.to_location,
                'usuario': prov.user,
                'pedido': prov.order,
                'grao': prov.grain,
                'preco_frete_total': prov.fullFreightPrice,
                'prazo_entrega': prov.deliveryDeadline,
                'prazo_entrega_fim': prov.deliveryDeadlineEnd,
                'dias_pagamento': prov.paymentDaysAfterDelivery,
                'pis_cofins': prov.pisCofins,
                'promotor': prov.promotor,
                'data_criacao': prov.createdAt,
                'data_atualizacao': prov.updatedAt
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def calcular_metricas(provisionings: List[Provisioning]) -> Dict[str, Any]:
        """Calcula métricas dos provisionamentos"""
        if not provisionings:
            return {}
        
        # Filtrar apenas grãos
        grain_provisionings = [p for p in provisionings if p.isGrain]
        freight_provisionings = [p for p in provisionings if p.isFreight]
        
        # Métricas básicas
        total_amount = sum(p.amount for p in provisionings if p.amount)
        total_remaining = sum(p.amountRemaining for p in provisionings if p.amountRemaining)
        
        # Valores
        total_value = sum(
            (p.amount * p.bagPrice) for p in provisionings 
            if p.amount and p.bagPrice
        )
        
        remaining_value = sum(
            (p.amountRemaining * p.bagPrice) for p in provisionings 
            if p.amountRemaining and p.bagPrice
        )
        
        # Preços
        prices = [p.bagPrice for p in provisionings if p.bagPrice]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        # Taxa de utilização
        utilization_rate = ((total_amount - total_remaining) / total_amount * 100) if total_amount > 0 else 0
        
        return {
            'total_provisionamentos': len(provisionings),
            'provisionamentos_grao': len(grain_provisionings),
            'provisionamentos_frete': len(freight_provisionings),
            'quantidade_total': total_amount,
            'quantidade_restante': total_remaining,
            'quantidade_utilizada': total_amount - total_remaining,
            'valor_total': total_value,
            'valor_restante': remaining_value,
            'valor_utilizado': total_value - remaining_value,
            'preco_medio': avg_price,
            'preco_minimo': min_price,
            'preco_maximo': max_price,
            'taxa_utilizacao': utilization_rate
        }
    
    @staticmethod
    def agrupar_por_usuario(provisionings: List[Provisioning]) -> pd.DataFrame:
        """Agrupa provisionamentos por usuário"""
        user_data = {}
        
        for prov in provisionings:
            user = prov.user or "Sem usuário"
            
            if user not in user_data:
                user_data[user] = {
                    'usuario': user,
                    'total_provisionamentos': 0,
                    'quantidade_total': 0,
                    'quantidade_restante': 0,
                    'valor_total': 0,
                    'valor_restante': 0
                }
            
            user_data[user]['total_provisionamentos'] += 1
            
            if prov.amount:
                user_data[user]['quantidade_total'] += prov.amount
            
            if prov.amountRemaining:
                user_data[user]['quantidade_restante'] += prov.amountRemaining
            
            if prov.amount and prov.bagPrice:
                user_data[user]['valor_total'] += prov.amount * prov.bagPrice
            
            if prov.amountRemaining and prov.bagPrice:
                user_data[user]['valor_restante'] += prov.amountRemaining * prov.bagPrice
        
        # Calcular taxa de utilização por usuário
        for user in user_data:
            total = user_data[user]['quantidade_total']
            remaining = user_data[user]['quantidade_restante']
            user_data[user]['taxa_utilizacao'] = ((total - remaining) / total * 100) if total > 0 else 0
        
        return pd.DataFrame(list(user_data.values()))
    
    @staticmethod
    def agrupar_por_grao(provisionings: List[Provisioning]) -> pd.DataFrame:
        """Agrupa provisionamentos por tipo de grão"""
        grain_data = {}
        
        for prov in provisionings:
            if not prov.isGrain:
                continue
                
            grain = prov.grain or "Não especificado"
            
            if grain not in grain_data:
                grain_data[grain] = {
                    'grao': grain,
                    'total_provisionamentos': 0,
                    'quantidade_total': 0,
                    'quantidade_restante': 0,
                    'valor_total': 0,
                    'preco_medio': 0
                }
            
            grain_data[grain]['total_provisionamentos'] += 1
            
            if prov.amount:
                grain_data[grain]['quantidade_total'] += prov.amount
            
            if prov.amountRemaining:
                grain_data[grain]['quantidade_restante'] += prov.amountRemaining
            
            if prov.amount and prov.bagPrice:
                grain_data[grain]['valor_total'] += prov.amount * prov.bagPrice
        
        # Calcular preço médio por grão
        for grain in grain_data:
            total_qty = grain_data[grain]['quantidade_total']
            total_value = grain_data[grain]['valor_total']
            grain_data[grain]['preco_medio'] = total_value / total_qty if total_qty > 0 else 0
        
        return pd.DataFrame(list(grain_data.values()))
    
    @staticmethod
    def get_provisionamentos_vencidos(provisionings: List[Provisioning]) -> List[Provisioning]:
        """Retorna provisionamentos com prazo vencido"""
        today = datetime.now()
        vencidos = []
        
        for prov in provisionings:
            if (prov.deliveryDeadline and 
                prov.amountRemaining and 
                prov.amountRemaining > 0):
                
                try:
                    if isinstance(prov.deliveryDeadline, str):
                        deadline = datetime.fromisoformat(prov.deliveryDeadline.replace('Z', '+00:00'))
                    else:
                        deadline = prov.deliveryDeadline
                    
                    if deadline < today:
                        vencidos.append(prov)
                except:
                    continue
        
        return vencidos
    
    @staticmethod
    def get_alertas_provisionamento(provisionings: List[Provisioning]) -> Dict[str, List]:
        """Gera alertas para provisionamentos"""
        alertas = {
            'vencidos': [],
            'baixo_estoque': [],
            'sem_movimento': [],
            'preco_alto': []
        }
        
        # Calcular preço médio geral
        prices = [p.bagPrice for p in provisionings if p.bagPrice and p.isGrain]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        for prov in provisionings:
            # Vencidos
            if prov.deliveryDeadline and prov.amountRemaining and prov.amountRemaining > 0:
                try:
                    if isinstance(prov.deliveryDeadline, str):
                        deadline = datetime.fromisoformat(prov.deliveryDeadline.replace('Z', '+00:00'))
                    else:
                        deadline = prov.deliveryDeadline
                    
                    if deadline < datetime.now():
                        alertas['vencidos'].append({
                            'id': prov._id,
                            'usuario': prov.user,
                            'quantidade_restante': prov.amountRemaining,
                            'prazo': deadline
                        })
                except:
                    pass
            
            # Baixo estoque (menos de 10% restante)
            if (prov.amount and prov.amountRemaining and 
                prov.amountRemaining / prov.amount < 0.1):
                alertas['baixo_estoque'].append({
                    'id': prov._id,
                    'usuario': prov.user,
                    'quantidade_total': prov.amount,
                    'quantidade_restante': prov.amountRemaining,
                    'percentual_restante': (prov.amountRemaining / prov.amount * 100)
                })
            
            # Sem movimento (quantidade restante = quantidade total)
            if (prov.amount and prov.amountRemaining and 
                prov.amountRemaining == prov.amount):
                alertas['sem_movimento'].append({
                    'id': prov._id,
                    'usuario': prov.user,
                    'quantidade': prov.amount,
                    'data_criacao': prov.createdAt
                })
            
            # Preço alto (acima de 20% da média)
            if (prov.bagPrice and avg_price > 0 and 
                prov.bagPrice > avg_price * 1.2):
                alertas['preco_alto'].append({
                    'id': prov._id,
                    'usuario': prov.user,
                    'preco': prov.bagPrice,
                    'preco_medio': avg_price,
                    'diferenca_percentual': ((prov.bagPrice - avg_price) / avg_price * 100)
                })
        
        return alertas

