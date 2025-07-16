"""
Página de Provisionamento - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from config.database import get_database_connection
from src.database_service_provisioning import ProvisioningService

def show_provisionamento_page():
    """Mostra página de provisionamento"""
    st.header("📦 Gestão de Provisionamento")
    
    # Obter dados de provisionamento
    db_config = get_database_connection()
    if not db_config:
        st.error("❌ Erro ao conectar com o banco de dados")
        return
    
    collections = db_config.get_collections()
    prov_service = ProvisioningService(collections)
    
    # Métricas principais
    with st.spinner("Carregando métricas de provisionamento..."):
        metricas = prov_service.get_metricas_provisionamento()
    
    if metricas:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Total Provisionamentos",
                value=metricas.get('total_provisionamentos', 0),
                delta=f"{metricas.get('provisionamentos_grao', 0)} grãos"
            )
        
        with col2:
            total_qty = metricas.get('quantidade_total', 0)
            remaining_qty = metricas.get('quantidade_restante', 0)
            st.metric(
                label="🌾 Quantidade Total",
                value=f"{total_qty:,.0f} sacas",
                delta=f"{remaining_qty:,.0f} restantes"
            )
        
        with col3:
            total_value = metricas.get('valor_total', 0)
            remaining_value = metricas.get('valor_restante', 0)
            st.metric(
                label="💰 Valor Total",
                value=f"R$ {total_value:,.2f}",
                delta=f"R$ {remaining_value:,.2f} restante"
            )
        
        with col4:
            utilization_rate = metricas.get('taxa_utilizacao', 0)
            avg_price = metricas.get('preco_medio', 0)
            st.metric(
                label="📊 Taxa Utilização",
                value=f"{utilization_rate:.1f}%",
                delta=f"R$ {avg_price:.2f} preço médio"
            )
    
    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filter = st.selectbox(
            "Tipo:",
            ["Todos", "🌾 Grão", "🚛 Frete", "❓ Outro"]
        )
    
    with col2:
        date_filter = st.date_input(
            "Data de criação (a partir de):",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col3:
        comprador_filter = st.text_input("Filtrar por comprador:")
    
    # Nova seção: Tabela agrupada por comprador e vendedor
    st.subheader("📊 Provisionamento por Comprador e Vendedor")
    
    # Carregar dados com unwind de sellersOrders
    with st.spinner("Carregando dados detalhados de provisionamento..."):
        df_grouped = prov_service.get_provisionings_grouped_dataframe(limit=1000)
    
    if not df_grouped.empty:
        # Aplicar filtros
        df_filtered = df_grouped.copy()
        
        if tipo_filter != "Todos":
            df_filtered = df_filtered[df_filtered['tipo'] == tipo_filter]
        
        if comprador_filter:
            df_filtered = df_filtered[
                df_filtered['comprador'].str.contains(comprador_filter, case=False, na=False)
            ]
        
        if date_filter:
            df_filtered = df_filtered[
                pd.to_datetime(df_filtered['data_criacao']).dt.date >= date_filter
            ]
        
        # Mostrar resultados
        st.subheader(f"📋 Resultados: {len(df_filtered)} registros de vendedores")
        
        if not df_filtered.empty:
            # Tabela principal agrupada
            st.dataframe(
                df_filtered[[
                    'comprador', 'vendedor', 'tipo', 'grao', 'preco_saca',
                    'quantidade_total_vendedor', 'quantidade_restante_vendedor', 
                    'quantidade_utilizada_vendedor', 'valor_total_vendedor',
                    'valor_restante_vendedor', 'taxa_utilizacao_vendedor',
                    'data_criacao', 'fob'
                ]],
                use_container_width=True,
                column_config={
                    'comprador': 'Comprador',
                    'vendedor': 'Vendedor',
                    'tipo': 'Tipo',
                    'grao': 'Grão',
                    'preco_saca': st.column_config.NumberColumn('Preço/Saca', format="R$ %.2f"),
                    'quantidade_total_vendedor': st.column_config.NumberColumn('Qtd Total', format="%.0f"),
                    'quantidade_restante_vendedor': st.column_config.NumberColumn('Qtd Restante', format="%.0f"),
                    'quantidade_utilizada_vendedor': st.column_config.NumberColumn('Qtd Utilizada', format="%.0f"),
                    'valor_total_vendedor': st.column_config.NumberColumn('Valor Total', format="R$ %.2f"),
                    'valor_restante_vendedor': st.column_config.NumberColumn('Valor Restante', format="R$ %.2f"),
                    'taxa_utilizacao_vendedor': st.column_config.NumberColumn('Taxa Utilização', format="%.1f%%"),
                    'data_criacao': 'Data Criação',
                    'fob': 'FOB'
                }
            )
            
            # Resumo agregado por comprador e vendedor
            st.subheader("📈 Resumo Agregado")
            
            # Agrupar por comprador e vendedor
            summary = df_filtered.groupby(['comprador', 'vendedor']).agg({
                'quantidade_total_vendedor': 'sum',
                'quantidade_restante_vendedor': 'sum',
                'quantidade_utilizada_vendedor': 'sum',
                'valor_total_vendedor': 'sum',
                'valor_restante_vendedor': 'sum'
            }).reset_index()
            
            # Calcular taxa de utilização agregada
            summary['taxa_utilizacao_agregada'] = (
                summary['quantidade_utilizada_vendedor'] / summary['quantidade_total_vendedor'] * 100
            ).fillna(0)
            
            st.dataframe(
                summary,
                use_container_width=True,
                column_config={
                    'comprador': 'Comprador',
                    'vendedor': 'Vendedor',
                    'quantidade_total_vendedor': st.column_config.NumberColumn('Total Sacas', format="%.0f"),
                    'quantidade_restante_vendedor': st.column_config.NumberColumn('Sacas Restantes', format="%.0f"),
                    'quantidade_utilizada_vendedor': st.column_config.NumberColumn('Sacas Utilizadas', format="%.0f"),
                    'valor_total_vendedor': st.column_config.NumberColumn('Valor Total', format="R$ %.2f"),
                    'valor_restante_vendedor': st.column_config.NumberColumn('Valor Restante', format="R$ %.2f"),
                    'taxa_utilizacao_agregada': st.column_config.NumberColumn('Taxa Utilização', format="%.1f%%")
                }
            )
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Top 10 Vendedores por Quantidade")
                
                # Agrupar por vendedor
                vendor_stats = df_filtered.groupby('vendedor').agg({
                    'quantidade_total_vendedor': 'sum',
                    'quantidade_restante_vendedor': 'sum'
                }).reset_index()
                
                vendor_stats = vendor_stats.sort_values('quantidade_total_vendedor', ascending=False).head(10)
                
                if not vendor_stats.empty:
                    fig = px.bar(
                        vendor_stats,
                        x='vendedor',
                        y=['quantidade_total_vendedor', 'quantidade_restante_vendedor'],
                        title="Quantidade Total vs Restante por Vendedor",
                        barmode='group'
                    )
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("💰 Top 10 Compradores por Valor")
                
                # Agrupar por comprador
                buyer_stats = df_filtered.groupby('comprador').agg({
                    'valor_total_vendedor': 'sum',
                    'valor_restante_vendedor': 'sum'
                }).reset_index()
                
                buyer_stats = buyer_stats.sort_values('valor_total_vendedor', ascending=False).head(10)
                
                if not buyer_stats.empty:
                    fig = px.bar(
                        buyer_stats,
                        x='comprador',
                        y=['valor_total_vendedor', 'valor_restante_vendedor'],
                        title="Valor Total vs Restante por Comprador",
                        barmode='group'
                    )
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas resumidas
            st.subheader("📊 Estatísticas Resumidas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_qty_filtered = df_filtered['quantidade_total_vendedor'].sum()
                st.metric("📦 Quantidade Total", f"{total_qty_filtered:,.0f}")
            
            with col2:
                total_remaining = df_filtered['quantidade_restante_vendedor'].sum()
                st.metric("📦 Quantidade Restante", f"{total_remaining:,.0f}")
            
            with col3:
                total_value_filtered = df_filtered['valor_total_vendedor'].sum()
                st.metric("💰 Valor Total", f"R$ {total_value_filtered:,.2f}")
            
            with col4:
                avg_utilization = df_filtered['taxa_utilizacao_vendedor'].mean()
                st.metric("📊 Utilização Média", f"{avg_utilization:.1f}%")
        
        else:
            st.info("Nenhum provisionamento encontrado com os filtros aplicados.")
    
    else:
        st.warning("Nenhum dado de provisionamento encontrado.")
    
    db_config.close_connection()

if __name__ == "__main__":
    show_provisionamento_page()

