"""
Página de Mapa - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from config.database import get_database_connection

def show_mapa_page():
    """Mostra página de mapa com endereços da Fox"""
    st.header("🗺️ Mapa de Endereços Fox")
    
    # Obter dados de endereços
    db_config = get_database_connection()
    if not db_config:
        st.error("❌ Erro ao conectar com o banco de dados")
        return
    
    collections = db_config.get_collections()
    
    # Buscar endereços na coleção addresses
    with st.spinner("Carregando endereços..."):
        try:
            addresses_collection = collections.get('addresses')
            if not addresses_collection:
                st.error("❌ Coleção 'addresses' não encontrada")
                db_config.close_connection()
                return
            
            # Buscar todos os endereços
            addresses = list(addresses_collection.find({}))
            
            if not addresses:
                st.warning("⚠️ Nenhum endereço encontrado na base de dados")
                db_config.close_connection()
                return
            
            # Converter para DataFrame para análise
            df_addresses = pd.DataFrame(addresses)
            
            # Mostrar estatísticas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📍 Total de Endereços", len(addresses))
            
            with col2:
                # Contar endereços com coordenadas
                with_coords = sum(1 for addr in addresses 
                                if addr.get('latitude') and addr.get('longitude'))
                st.metric("🎯 Com Coordenadas", with_coords)
            
            with col3:
                # Contar tipos únicos se existir campo type
                unique_types = len(set(addr.get('type', 'N/A') for addr in addresses))
                st.metric("🏢 Tipos Únicos", unique_types)
            
            # Criar mapa
            st.subheader("🗺️ Mapa Interativo")
            
            # Coordenadas centrais do Brasil (aproximadamente)
            center_lat = -14.2350
            center_lon = -51.9253
            
            # Verificar se há endereços com coordenadas válidas
            valid_addresses = []
            for addr in addresses:
                lat = addr.get('latitude')
                lon = addr.get('longitude')
                
                # Verificar se as coordenadas são válidas
                if lat and lon:
                    try:
                        lat_float = float(lat)
                        lon_float = float(lon)
                        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                            valid_addresses.append({
                                **addr,
                                'lat': lat_float,
                                'lon': lon_float
                            })
                    except (ValueError, TypeError):
                        continue
            
            if valid_addresses:
                # Calcular centro baseado nos endereços válidos
                avg_lat = sum(addr['lat'] for addr in valid_addresses) / len(valid_addresses)
                avg_lon = sum(addr['lon'] for addr in valid_addresses) / len(valid_addresses)
                center_lat = avg_lat
                center_lon = avg_lon
                
                # Criar mapa Folium
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=6,
                    tiles='OpenStreetMap'
                )
                
                # Adicionar marcadores para cada endereço
                for addr in valid_addresses:
                    # Preparar informações do popup
                    popup_info = []
                    
                    # Nome/Título
                    name = addr.get('name', addr.get('title', addr.get('address', 'Endereço Fox')))
                    popup_info.append(f"<b>{name}</b>")
                    
                    # Endereço completo
                    if addr.get('address'):
                        popup_info.append(f"📍 {addr['address']}")
                    
                    # Cidade/Estado
                    city = addr.get('city', '')
                    state = addr.get('state', '')
                    if city or state:
                        location = f"{city}, {state}".strip(', ')
                        if location:
                            popup_info.append(f"🏙️ {location}")
                    
                    # CEP
                    if addr.get('zipCode'):
                        popup_info.append(f"📮 CEP: {addr['zipCode']}")
                    
                    # Tipo
                    if addr.get('type'):
                        popup_info.append(f"🏢 Tipo: {addr['type']}")
                    
                    # Telefone
                    if addr.get('phone'):
                        popup_info.append(f"📞 {addr['phone']}")
                    
                    # Email
                    if addr.get('email'):
                        popup_info.append(f"📧 {addr['email']}")
                    
                    # Criar popup HTML
                    popup_html = "<br>".join(popup_info)
                    
                    # Definir cor do marcador baseado no tipo
                    icon_color = 'blue'
                    if addr.get('type'):
                        type_lower = str(addr['type']).lower()
                        if 'sede' in type_lower or 'matriz' in type_lower:
                            icon_color = 'red'
                        elif 'filial' in type_lower:
                            icon_color = 'green'
                        elif 'armazem' in type_lower or 'deposito' in type_lower:
                            icon_color = 'orange'
                    
                    # Adicionar marcador
                    folium.Marker(
                        location=[addr['lat'], addr['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=name,
                        icon=folium.Icon(color=icon_color, icon='building', prefix='fa')
                    ).add_to(m)
                
                # Exibir mapa
                map_data = st_folium(m, width=700, height=500)
                
                st.success(f"✅ {len(valid_addresses)} endereços exibidos no mapa")
                
            else:
                st.warning("⚠️ Nenhum endereço com coordenadas válidas encontrado")
                
                # Mostrar mapa vazio centrado no Brasil
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=4,
                    tiles='OpenStreetMap'
                )
                
                st_folium(m, width=700, height=500)
            
            # Tabela de endereços
            st.subheader("📋 Lista de Endereços")
            
            # Preparar dados para exibição
            display_data = []
            for addr in addresses:
                display_data.append({
                    'Nome': addr.get('name', addr.get('title', 'N/A')),
                    'Endereço': addr.get('address', 'N/A'),
                    'Cidade': addr.get('city', 'N/A'),
                    'Estado': addr.get('state', 'N/A'),
                    'CEP': addr.get('zipCode', 'N/A'),
                    'Tipo': addr.get('type', 'N/A'),
                    'Telefone': addr.get('phone', 'N/A'),
                    'Email': addr.get('email', 'N/A'),
                    'Latitude': addr.get('latitude', 'N/A'),
                    'Longitude': addr.get('longitude', 'N/A')
                })
            
            df_display = pd.DataFrame(display_data)
            
            # Exibir tabela
            st.dataframe(
                df_display,
                use_container_width=True,
                column_config={
                    'Nome': 'Nome/Título',
                    'Endereço': 'Endereço Completo',
                    'Cidade': 'Cidade',
                    'Estado': 'Estado',
                    'CEP': 'CEP',
                    'Tipo': 'Tipo',
                    'Telefone': 'Telefone',
                    'Email': 'Email',
                    'Latitude': st.column_config.NumberColumn('Latitude', format="%.6f"),
                    'Longitude': st.column_config.NumberColumn('Longitude', format="%.6f")
                }
            )
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar endereços: {str(e)}")
        
        finally:
            db_config.close_connection()

if __name__ == "__main__":
    show_mapa_page()

