import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Mi Inventario Pro", page_icon="🏠", layout="wide")

ARCHIVO_DB = 'inventario_bodega.json'
CARPETA_FOTOS = 'fotos_bultos' # Carpeta donde se guardarán las imagenes

# Asegurar que existe la carpeta de fotos
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

# --- 2. FUNCIONES ---
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

def guardar_imagen(uploaded_file, id_bulto):
    """Guarda la imagen subida con el nombre del ID"""
    if uploaded_file is None:
        return None
    
    # Obtenemos la extensión (jpg, png, etc)
    file_ext = uploaded_file.name.split('.')[-1]
    nombre_archivo = f"{id_bulto}.{file_ext}"
    ruta_completa = os.path.join(CARPETA_FOTOS, nombre_archivo)
    
    # Guardamos el archivo físico
    with open(ruta_completa, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return ruta_completa

def obtener_icono(tipo):
    mapa = {"Caja": "📦", "Bolsa": "🛍️", "Maleta": "🧳", "Mueble": "🗄️", "Otro": "🔖"}
    return mapa.get(tipo, "📦")

if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_datos()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("Gestión")
    tab_add, tab_del = st.tabs(["➕ Nuevo", "🗑️ Borrar"])
    
    # --- PESTAÑA AGREGAR ---
    with tab_add:
        with st.form("form_agregar", clear_on_submit=True):
            col_id, col_tipo = st.columns([1, 1])
            with col_id:
                id_input = st.text_input("ID", placeholder="Ej: C-01").upper()
            with col_tipo:
                tipo_input = st.selectbox("Tipo", ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"])
            
            ubicacion_input = st.text_input("📍 Ubicación", placeholder="Ej: Estante 2")
            contenido_input = st.text_area("📝 Contenido", placeholder="Lista de objetos...")
            
            # --- NUEVO: SUBIDA DE FOTO ---
            foto_input = st.file_uploader("📸 Foto de referencia", type=['png', 'jpg', 'jpeg'])
            
            btn_guardar = st.form_submit_button("Guardar Item", use_container_width=True)
            
            if btn_guardar:
                if id_input and contenido_input:
                    ids_existentes = [item['id'] for item in st.session_state.inventario]
                    if id_input in ids_existentes:
                        st.error("⚠️ El ID ya existe.")
                    else:
                        # Guardamos la foto primero
                        ruta_foto = guardar_imagen(foto_input, id_input)
                        
                        nuevo = {
                            "id": id_input,
                            "tipo": tipo_input,
                            "contenido": contenido_input,
                            "ubicacion": ubicacion_input,
                            "ruta_foto": ruta_foto, # Guardamos la ruta en el JSON
                            "fecha": time.strftime("%Y-%m-%d")
                        }
                        st.session_state.inventario.append(nuevo)
                        guardar_datos(st.session_state.inventario)
                        st.toast(f"¡{id_input} guardado!", icon='✅')
                        time.sleep(1)
                        st.rerun()
                else:
                    st.toast("Faltan datos obligatorios", icon='❌')

    # --- PESTAÑA BORRAR ---
    with tab_del:
        lista_ids = [item['id'] for item in st.session_state.inventario]
        if lista_ids:
            id_borrar = st.selectbox("ID a borrar", lista_ids)
            if st.button("Eliminar Definitivamente", type="primary"):
                # Opcional: Borrar también la foto física para no acumular basura
                item_a_borrar = next((x for x in st.session_state.inventario if x['id'] == id_borrar), None)
                if item_a_borrar and item_a_borrar.get('ruta_foto'):
                    if os.path.exists(item_a_borrar['ruta_foto']):
                        os.remove(item_a_borrar['ruta_foto'])

                st.session_state.inventario = [x for x in st.session_state.inventario if x['id'] != id_borrar]
                guardar_datos(st.session_state.inventario)
                st.toast("Eliminado", icon='🗑️')
                st.rerun()

# --- 4. PANEL PRINCIPAL ---
st.title("🏠 Inventario Visual")
st.markdown("---")

if not st.session_state.inventario:
    st.info("👋 Inventario vacío. Agrega items con fotos desde la izquierda.")
else:
    # Métricas
    df = pd.DataFrame(st.session_state.inventario)
    col1, col2 = st.columns(2)
    col1.metric("Total Bultos", len(df))
    col2.metric("Ubicaciones", df['ubicacion'].nunique())

    # --- BUSCADOR VISUAL ---
    st.divider()
    busqueda = st.text_input("🔍 Buscar objeto (te mostraré la foto del contenedor)", placeholder="Ej: Taladro...")

    if busqueda:
        # Filtro
        mask = (
            df['contenido'].str.contains(busqueda, case=False, na=False) | 
            df['id'].str.contains(busqueda, case=False, na=False)
        )
        resultados = df[mask]
        
        if not resultados.empty:
            st.success(f"Encontrado en {len(resultados)} contenedor(es):")
            
            # --- VISTA DE RESULTADOS CON TARJETAS ---
            for index, row in resultados.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    
                    with c1:
                        # MOSTRAR FOTO SI EXISTE
                        if row.get('ruta_foto') and os.path.exists(row['ruta_foto']):
                            st.image(row['ruta_foto'], use_container_width=True)
                        else:
                            # Si no hay foto, ponemos un icono gigante
                            st.markdown(f"<h1 style='text-align: center;'>{obtener_icono(row['tipo'])}</h1>", unsafe_allow_html=True)
                    
                    with c2:
                        st.subheader(f"{row['id']} - {row['tipo']}")
                        st.caption(f"📍 {row['ubicacion']}")
                        st.write(f"**Contiene:** {row['contenido']}")
        else:
            st.warning("No se encontró nada.")
            
    else:
        # Si no busca nada, mostramos la tabla resumen simple
        st.subheader("📋 Resumen General")
        st.dataframe(
            df[['id', 'tipo', 'ubicacion', 'contenido']], 
            use_container_width=True, 
            hide_index=True
        )
