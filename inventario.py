import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image

# --- 1. CONFIGURACIÓN INICIAL DE LA PÁGINA ---
st.set_page_config(
    page_title="Mi Inventario Pro", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definimos nombres de archivos y carpetas
ARCHIVO_DB = 'inventario_bodega.json'
CARPETA_FOTOS = 'fotos_bultos' 

# Crear carpeta de fotos si no existe
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

# --- 2. FUNCIONES DE EL SISTEMA ---

def cargar_datos():
    """Carga los datos del JSON. Si no existe, retorna lista vacía."""
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_datos(lista_inventario):
    """Escribe la lista actualizada en el JSON."""
    with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
        json.dump(lista_inventario, f, indent=4, ensure_ascii=False)

def guardar_imagen(uploaded_file, id_bulto):
    """Guarda la imagen subida en la carpeta y retorna la ruta."""
    if uploaded_file is None:
        return None
    
    # Extraer extensión (jpg, png)
    file_ext = uploaded_file.name.split('.')[-1]
    nombre_archivo = f"{id_bulto}.{file_ext}"
    ruta_completa = os.path.join(CARPETA_FOTOS, nombre_archivo)
    
    # Escribir archivo en disco
    with open(ruta_completa, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return ruta_completa

def obtener_icono(tipo):
    """Devuelve un emoji según el tipo de contenedor."""
    mapa = {
        "Caja": "📦", 
        "Bolsa": "🛍️", 
        "Maleta": "🧳", 
        "Mueble": "🗄️", 
        "Otro": "🔖"
    }
    return mapa.get(tipo, "📦")

# --- 3. INICIALIZAR ESTADO (MEMORIA) ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_datos()

# --- 4. BARRA LATERAL: GESTIÓN (AGREGAR, EDITAR, BORRAR) ---
with st.sidebar:
    st.title("🗂️ Gestión")
    
    # Pestañas para organizar las acciones
    tab_add, tab_edit, tab_del = st.tabs(["➕ Nuevo", "✏️ Editar", "🗑️ Borrar"])
    
    # >>> PESTAÑA 1: AGREGAR <<<
    with tab_add:
        st.caption("Registrar nuevo bulto")
        with st.form("form_agregar", clear_on_submit=True):
            col_id, col_tipo = st.columns([1, 1])
            with col_id:
                id_input = st.text_input("ID Nuevo", placeholder="Ej: C-01").upper().strip()
            with col_tipo:
                tipo_input = st.selectbox("Tipo", ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"])
            
            ubicacion_input = st.text_input("📍 Ubicación", placeholder="Ej: Estante 2")
            contenido_input = st.text_area("📝 Contenido", placeholder="Lista de objetos...")
            foto_input = st.file_uploader("📸 Foto (Opcional)", type=['png', 'jpg', 'jpeg'], key="foto_new")
            
            # Botón de guardar
            if st.form_submit_button("Guardar Item", use_container_width=True):
                if id_input and contenido_input:
                    # Validar duplicados
                    ids_existentes = [item['id'] for item in st.session_state.inventario]
                    if id_input in ids_existentes:
                        st.error("⚠️ El ID ya existe.")
                    else:
                        ruta_foto = guardar_imagen(foto_input, id_input)
                        nuevo = {
                            "id": id_input,
                            "tipo": tipo_input,
                            "contenido": contenido_input,
                            "ubicacion": ubicacion_input,
                            "ruta_foto": ruta_foto,
                            "fecha": time.strftime("%Y-%m-%d")
                        }
                        st.session_state.inventario.append(nuevo)
                        guardar_datos(st.session_state.inventario)
                        st.toast(f"¡{id_input} guardado!", icon='✅')
                        time.sleep(1)
                        st.rerun()
                else:
                    st.toast("Faltan datos obligatorios", icon='❌')

    # >>> PESTAÑA 2: EDITAR <<<
    with tab_edit:
        st.caption("Modificar existente")
        lista_ids = [item['id'] for item in st.session_state.inventario]
        
        if lista_ids:
            # 1. Seleccionar ID
            id_a_editar = st.selectbox("Selecciona ID a editar:", lista_ids)
            
            # 2. Obtener datos actuales
            item_actual = next((x for x in st.session_state.inventario if x['id'] == id_a_editar), None)
            
            if item_actual:
                with st.form("form_editar"):
                    st.write(f"Editando: **{id_a_editar}**")
                    
                    # Índices para los selectbox
                    opciones_tipo = ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"]
                    try:
                        idx_tipo = opciones_tipo.index(item_actual['tipo'])
                    except:
                        idx_tipo = 0
                        
                    new_tipo = st.selectbox("Tipo", opciones_tipo, index=idx_tipo)
                    new_ubicacion = st.text_input("Ubicación", value=item_actual['ubicacion'])
                    new_contenido = st.text_area("Contenido", value=item_actual['contenido'], height=100)
                    
                    st.markdown("---")
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        st.caption("Foto actual:")
                        if item_actual.get('ruta_foto') and os.path.exists(item_actual['ruta_foto']):
                            st.image(item_actual['ruta_foto'], width=100)
                        else:
                            st.write("🚫 Sin foto")
                    with col_f2:
                        new_foto = st.file_uploader("Cambiar Foto", type=['png', 'jpg', 'jpeg'], key="foto_edit")
                    
                    if st.form_submit_button("💾 Actualizar Cambios", type="primary", use_container_width=True):
                        # Actualizar diccionario en memoria
                        item_actual['tipo'] = new_tipo
                        item_actual['ubicacion'] = new_ubicacion
                        item_actual['contenido'] = new_contenido
                        
                        if new_foto:
                            nueva_ruta = guardar_imagen(new_foto, id_a_editar)
                            item_actual['ruta_foto'] = nueva_ruta
                        
                        guardar_datos(st.session_state.inventario)
                        st.toast("¡Datos actualizados!", icon='🔄')
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("No hay items para editar.")

    # >>> PESTAÑA 3: BORRAR <<<
    with tab_del:
        st.caption("Eliminar definitivamente")
        if lista_ids:
            id_borrar = st.selectbox("Seleccionar ID para borrar:", lista_ids, key="del_select")
            
            if st.button("🗑️ Eliminar Item", type="primary", use_container_width=True):
                # Encontrar item para borrar foto si existe
                item_a_borrar = next((x for x in st.session_state.inventario if x['id'] == id_borrar), None)
                if item_a_borrar and item_a_borrar.get('ruta_foto'):
                    if os.path.exists(item_a_borrar['ruta_foto']):
                        try:
                            os.remove(item_a_borrar['ruta_foto'])
                        except:
                            pass 
                            
                # Filtrar lista para quitar el elemento
                st.session_state.inventario = [x for x in st.session_state.inventario if x['id'] != id_borrar]
                guardar_datos(st.session_state.inventario)
                st.toast("Elemento eliminado", icon='🗑️')
                time.sleep(0.5)
                st.rerun()
        else:
            st.info("Inventario vacío.")

# --- 5. PANEL PRINCIPAL (VISUALIZACIÓN) ---
st.title("🏠 Inventario Visual")
st.markdown("---")

if not st.session_state.inventario:
    st.info("👋 Tu inventario está vacío. Usa el menú lateral para agregar tu primera caja o bolsa.")
else:
    # --- MÉTRICAS SUPERIORES ---
    df = pd.DataFrame(st.session_state.inventario)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Bultos", len(df))
    col2.metric("📍 Ubicaciones", df['ubicacion'].nunique())
    # Manejo seguro de fecha
    ultima_fecha = df.iloc[-1]['fecha'] if 'fecha' in df.columns else "N/A"
    col3.metric("📅 Último Registro", ultima_fecha)

    st.divider()

    # --- BUSCADOR ---
    busqueda = st.text_input("🔍 Buscar (Nombre de objeto, ID o Ubicación)", placeholder="Ej: Adornos de navidad, taladro...")

    if busqueda:
        # Lógica de búsqueda flexible
        mask = (
            df['contenido'].str.contains(busqueda, case=False, na=False) | 
            df['id'].str.contains(busqueda, case=False, na=False) |
            df['ubicacion'].str.contains(busqueda, case=False, na=False)
        )
        resultados = df[mask]
        
        if not resultados.empty:
            st.success(f"✅ Encontrado en **{len(resultados)}** lugar(es):")
            
            # --- VISTA DE TARJETAS (CARD VIEW) PARA RESULTADOS ---
            for index, row in resultados.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    
                    with c1:
                        # Mostrar Foto o Icono Grande
                        if row.get('ruta_foto') and os.path.exists(row['ruta_foto']):
                            st.image(row['ruta_foto'], use_container_width=True)
                        else:
                            # Icono gigante si no hay foto
                            st.markdown(f"<div style='text-align:center; font-size: 50px;'>{obtener_icono(row['tipo'])}</div>", unsafe_allow_html=True)
                    
                    with c2:
                        st.subheader(f"{row['id']} - {row['tipo']}")
                        st.markdown(f"**📍 Ubicación:** `{row['ubicacion']}`")
                        st.markdown(f"**📝 Contiene:** {row['contenido']}")
        else:
            st.warning("🚫 No encontré coincidencias con esa búsqueda.")
            
    else:
        # --- VISTA DE TABLA GENERAL (SI NO HAY BÚSQUEDA) ---
        st.subheader("📋 Listado Completo")
        
        # Copia para visualización limpia
        df_vista = df.copy()
        df_vista['Icono'] = df_vista['tipo'].apply(obtener_icono)
        
        st.dataframe(
            df_vista,
            column_order=("id", "Icono", "tipo", "ubicacion", "contenido"),
            column_config={
                "id": st.column_config.TextColumn("ID", width="small"),
                "Icono": st.column_config.TextColumn("", width="small"),
                "tipo": st.column_config.TextColumn("Tipo", width="small"),
                "ubicacion": st.column_config.TextColumn("Ubicación", width="medium"),
                "contenido": st.column_config.TextColumn("Contenido", width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
