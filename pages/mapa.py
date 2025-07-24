"""
Página de Mapa - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
from config.database import get_database_connection

# Import condicional do folium
try:
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

def get_addresses_with_cities(collections):
    """Busca endereços com lookup de cities para melhor performance"""
    try:
        addresses_collection = collections.get('addresses')
        if addresses_collection is None:
            return None
        
        # Pipeline de agregação com lookup de cities
        pipeline = [
            # Lookup com cities
            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city",
                    "foreignField": "_id",
                    "as": "city_info"
                }
            },
            # Adicionar campos calculados
            {
                "$addFields": {
                    "city_name": {"$arrayElemAt": ["$city_info.name", 0]},
                    "state_name": {"$arrayElemAt": ["$city_info.state", 0]},
                    "has_coordinates": {
                        "$and": [
                            {"$ne": ["$location", None]},
                            {"$ne": ["$location.coordinates", None]},
                            {"$gte": [{"$size": {"$ifNull": ["$location.coordinates", []]}}, 2]}
                        ]
                    }
                }
            },
            # Projetar apenas campos necessários
            {
                "$project": {
                    "name": 1,
                    "type": 1,
                    "address": 1,
                    "city_name": 1,
                    "state_name": 1,
                    "zipCode": 1,
                    "phone": 1,
                    "email": 1,
                    "location": 1,
                    "has_coordinates": 1,
                    "isActive": 1,
                    "createdAt": 1,
                    "updatedAt": 1
                }
            }
        ]
        
        # Executar agregação
        addresses = list(addresses_collection.aggregate(pipeline))
        return addresses
        
    except Exception as e:
        st.error(f"❌ Erro na consulta de endereços: {str(e)}")
        return None

def show_mapa_page():
    """Mostra página de mapa com endereços da Fox"""
    st.header("🗺️ Mapa de Endereços Fox")
    
    # Verificar se folium está disponível
    if not FOLIUM_AVAILABLE:
        st.error("❌ **Dependências de mapa não instaladas**")
        st.markdown("""
        Para usar a funcionalidade de mapa, você precisa instalar as dependências necessárias:
        
        ```bash
        pip install folium streamlit-folium
        ```
        
        Ou instale todas as dependências do projeto:
        
        ```bash
        pip install -r requirements.txt
        ```
        
        Após a instalação, reinicie a aplicação.
        """)
        return
    
    # Obter dados de endereços
    db_config = get_database_connection()
    if not db_config:
        st.error("❌ Erro ao conectar com o banco de dados")
        return
    
    collections = db_config.get_collections()
    
    # Buscar endereços na coleção addresses com lookup de cities
    with st.spinner("Carregando endereços..."):
        try:
            # Usar função otimizada com lookup
            addresses = get_addresses_with_cities(collections)
            
            if addresses is None:
                st.error("❌ Coleção 'addresses' não encontrada")
                db_config.close_connection()
                return
            
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
                # Contar endereços com coordenadas (usando campo calculado)
                with_coords = sum(1 for addr in addresses if addr.get('has_coordinates', False))
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
            
            # Filtrar endereços com coordenadas válidas (otimizado)
            valid_addresses = []
            for addr in addresses:
                # Usar campo calculado para performance
                if not addr.get('has_coordinates', False):
                    continue
                    
                coordinates = addr.get('location', {}).get('coordinates', [])
                if len(coordinates) >= 2:
                    try:
                        lon_float = float(coordinates[0])  # longitude
                        lat_float = float(coordinates[1])  # latitude
                        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                            valid_addresses.append({
                                **addr,
                                'lat': lat_float,
                                'lon': lon_float
                            })
                    except (ValueError, TypeError, IndexError):
                        continue
            
            if valid_addresses:
                # Calcular centro baseado nos endereços válidos
                avg_lat = sum(addr['lat'] for addr in valid_addresses) / len(valid_addresses)
                avg_lon = sum(addr['lon'] for addr in valid_addresses) / len(valid_addresses)
                center_lat = avg_lat
                center_lon = avg_lon
                
                # Criar mapa Folium com clusterização
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=6,
                    tiles='OpenStreetMap'
                )
                
                # Criar cluster de marcadores para melhor performance
                marker_cluster = MarkerCluster(
                    name="Endereços Fox",
                    overlay=True,
                    control=True,
                    icon_create_function=None
                ).add_to(m)
                
                # Adicionar marcadores clusterizados
                for addr in valid_addresses:
                    # Preparar informações do popup
                    popup_info = []
                    
                    # Nome/Título
                    name = addr.get('name', addr.get('title', addr.get('address', 'Endereço Fox')))
                    popup_info.append(f"<b>{name}</b>")
                    
                    # Endereço completo
                    if addr.get('address'):
                        popup_info.append(f"📍 {addr['address']}")
                    
                    # Cidade/Estado (usando dados do lookup)
                    city_name = addr.get('city_name', '')
                    state_name = addr.get('state_name', '')
                    if city_name or state_name:
                        location_str = f"{city_name}, {state_name}".strip(', ')
                        if location_str:
                            popup_info.append(f"🏙️ {location_str}")
                    
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
                        elif 'armazem' in type_lower or 'deposito' in type_lower or 'industria' in type_lower:
                            icon_color = 'orange'
                    
                    # Adicionar marcador ao cluster
                    folium.Marker(
                        location=[addr['lat'], addr['lon']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=name,
                        icon=folium.Icon(color=icon_color, icon='building', prefix='fa')
                    ).add_to(marker_cluster)
                
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
            
            # Preparar dados para exibição (usando dados do lookup)
            display_data = []
            for addr in addresses:
                coordinates = addr.get('location', {}).get('coordinates', [])
                
                # Extrair latitude e longitude do array coordinates (formato GeoJSON)
                latitude = coordinates[1] if len(coordinates) >= 2 else 'N/A'
                longitude = coordinates[0] if len(coordinates) >= 2 else 'N/A'
                
                display_data.append({
                    'Nome': addr.get('name', addr.get('title', 'N/A')),
                    'Endereço': addr.get('address', 'N/A'),
                    'Cidade': addr.get('city_name', 'N/A'),  # Usando lookup
                    'Estado': addr.get('state_name', 'N/A'),  # Usando lookup
                    'CEP': addr.get('zipCode', 'N/A'),
                    'Tipo': addr.get('type', 'N/A'),
                    'Telefone': addr.get('phone', 'N/A'),
                    'Email': addr.get('email', 'N/A'),
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Com Coordenadas': 'Sim' if addr.get('has_coordinates', False) else 'Não'
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
                    'Longitude': st.column_config.NumberColumn('Longitude', format="%.6f"),
                    'Com Coordenadas': 'Tem Coordenadas'
                }
            )
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar endereços: {str(e)}")
        
        finally:
            db_config.close_connection()

if __name__ == "__main__":
    show_mapa_page()

