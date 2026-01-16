import streamlit as st
import pandas as pd
import json
import os
import time

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Mi Inventario Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNCIONES DE PERSISTENCIA (JSON) ---
ARCHIVO_DB = 'inventario_bodega.json'

def cargar_datos():
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_datos(lista_inventario):
    with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
        json.dump(lista_inventario, f, indent=4, ensure_ascii=False)

# Inicializar estado
if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_datos()

# --- 3. ESTILOS Y AYUDAS VISUALES ---
def obtener_icono(tipo):
    """Asigna un emoji según el tipo de contenedor"""
    mapa = {
        "Caja": "📦",
        "Bolsa": "🛍️",
        "Maleta": "🧳",
        "Mueble": "🗄️",
        "Otro": "🔖"
    }
    return mapa.get(tipo, "📦")

# --- 4. BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/679/679720.png", width=50)
    st.title("Gestión")
    
    tab_add, tab_del = st.tabs(["➕ Nuevo", "🗑️ Borrar"])
    
    # --- PESTAÑA AGREGAR ---
    with tab_add:
        st.write("Registra un nuevo bulto")
        with st.form("form_agregar", clear_on_submit=True):
            col_id, col_tipo = st.columns([1, 1])
            with col_id:
                id_input = st.text_input("ID", placeholder="Ej: C-01").upper()
            with col_tipo:
                tipo_input = st.selectbox("Tipo", ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"])
            
            ubicacion_input = st.text_input("📍 Ubicación", placeholder="Ej: Estante 2 - Nivel 3")
            contenido_input = st.text_area("📝 Contenido", placeholder="Lista de objetos...", height=100)
            
            btn_guardar = st.form_submit_button("Guardar Item", use_container_width=True)
            
            if btn_guardar:
                if id_input and contenido_input:
                    ids_existentes = [item['id'] for item in st.session_state.inventario]
                    if id_input in ids_existentes:
                        st.error("⚠️ El ID ya existe.")
                    else:
                        nuevo = {
                            "id": id_input,
                            "tipo": tipo_input,
                            "contenido": contenido_input,
                            "ubicacion": ubicacion_input,
                            "fecha": time.strftime("%Y-%m-%d") # Agregamos fecha de creación
                        }
                        st.session_state.inventario.append(nuevo)
                        guardar_datos(st.session_state.inventario)
                        st.toast(f"¡{id_input} guardado con éxito!", icon='✅')
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.toast("Faltan datos obligatorios", icon='❌')

    # --- PESTAÑA BORRAR ---
    with tab_del:
        st.write("Eliminar un bulto")
        lista_ids = [item['id'] for item in st.session_state.inventario]
        
        if lista_ids:
            id_borrar = st.selectbox("Seleccionar ID", lista_ids)
            if st.button("Eliminar Definitivamente", type="primary", use_container_width=True):
                st.session_state.inventario = [x for x in st.session_state.inventario if x['id'] != id_borrar]
                guardar_datos(st.session_state.inventario)
                st.toast(f"Item {id_borrar} eliminado", icon='🗑️')
                time.sleep(0.5)
                st.rerun()
        else:
            st.info("Nada que borrar.")

    st.divider()
    st.caption("v2.0 - Sistema de Bodega")

# --- 5. PANEL PRINCIPAL ---

# Título y Header
st.title("🏠 Inventario de Casa")
st.markdown("---")

# Métricas (KPIs)
if st.session_state.inventario:
    df = pd.DataFrame(st.session_state.inventario)
    
    # Cálculos rápidos
    total_bultos = len(df)
    total_ubicaciones = df['ubicacion'].nunique()
    ultimo_agregado = df.iloc[-1]['id'] if not df.empty else "N/A"

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("📦 Total Bultos", total_bultos)
    kpi2.metric("📍 Ubicaciones", total_ubicaciones)
    kpi3.metric("🕒 Último Agregado", ultimo_agregado)
else:
    st.info("👋 ¡Bienvenido! Empieza agregando cosas en el menú lateral.")

st.write("") # Espacio

# --- 6. BUSCADOR Y VISUALIZACIÓN ---
col_search, col_filter = st.columns([3, 1])

with col_search:
    busqueda = st.text_input("🔍 ¿Qué estás buscando?", placeholder="Ej: Taladro, adornos, herramientas...")

# Filtrado de datos
if st.session_state.inventario:
    df_show = pd.DataFrame(st.session_state.inventario)
    
    # Crear columna visual con Icono + Tipo
    df_show['Visual_Tipo'] = df_show['tipo'].apply(lambda x: f"{obtener_icono(x)} {x}")

    # Lógica de búsqueda
    if busqueda:
        mask = (
            df_show['contenido'].str.contains(busqueda, case=False, na=False) | 
            df_show['id'].str.contains(busqueda, case=False, na=False)
        )
        df_final = df_show[mask]
        msg_result = f"✅ Se encontraron **{len(df_final)}** resultados"
    else:
        df_final = df_show
        msg_result = "📋 Vista general del inventario"

    st.caption(msg_result)

    # --- TABLA AVANZADA (DATAFRAME) ---
    st.dataframe(
        df_final,
        column_order=("id", "Visual_Tipo", "ubicacion", "contenido"), # Orden de columnas
        column_config={
            "id": st.column_config.TextColumn(
                "Identificador",
                help="ID único de la caja/bolsa",
                width="small",
                validate="^[A-Za-z0-9]+$"
            ),
            "Visual_Tipo": st.column_config.TextColumn(
                "Tipo",
                width="small"
            ),
            "ubicacion": st.column_config.TextColumn(
                "📍 Ubicación",
                width="medium"
            ),
            "contenido": st.column_config.TextColumn(
                "📝 Contenido",
                width="large"
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=400 # Altura fija para que se vea como app
    )
