import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURACIÓN Y FUNCIONES DE GUARDADO ---
ARCHIVO_DB = 'inventario_bodega.json'

def cargar_datos():
    """Carga la lista de diccionarios desde el archivo JSON si existe."""
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] 
    return []

def guardar_datos(lista_inventario):
    """Guarda la lista de diccionarios en el archivo JSON."""
    with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
        json.dump(lista_inventario, f, indent=4, ensure_ascii=False)

# Configuración de página
st.set_page_config(page_title="Inventario Permanente", layout="wide", page_icon="📦")
st.title("📦 Inventario de Bodega")

# --- CARGAR DATOS AL INICIO ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_datos()

# --- BARRA LATERAL: GESTIÓN (REGISTRAR Y ELIMINAR) ---
with st.sidebar:
    st.header("Gestión de Inventario")
    
    # Creamos dos pestañas para organizar las acciones
    tab_agregar, tab_eliminar = st.tabs(["➕ Registrar", "🗑️ Eliminar"])
    
    # --- PESTAÑA 1: AGREGAR ---
    with tab_agregar:
        with st.form("nuevo_item", clear_on_submit=True):
            id_input = st.text_input("ID Único (Ej: CAJA-01)", placeholder="Escribe el ID...")
            tipo_input = st.selectbox("Tipo", ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"])
            contenido_input = st.text_area("Contenido", placeholder="Ej: Luces, esferas...")
            ubicacion_input = st.text_input("Ubicación", placeholder="Ej: Estante 1")
            
            enviar = st.form_submit_button("💾 Guardar")
            
            if enviar:
                if id_input and contenido_input:
                    ids_existentes = [item['id'] for item in st.session_state.inventario]
                    
                    if id_input in ids_existentes:
                        st.error(f"¡Error! El ID '{id_input}' ya existe.")
                    else:
                        nuevo_item = {
                            "id": id_input,
                            "tipo": tipo_input,
                            "contenido": contenido_input,
                            "ubicacion": ubicacion_input
                        }
                        st.session_state.inventario.append(nuevo_item)
                        guardar_datos(st.session_state.inventario)
                        st.success(f"¡{id_input} guardado!")
                        st.rerun() # Recargamos para actualizar tablas al instante
                else:
                    st.warning("ID y Contenido son obligatorios.")

    # --- PESTAÑA 2: ELIMINAR ---
    with tab_eliminar:
        st.write("Selecciona la caja o bolsa que quieres dar de baja.")
        
        # Obtenemos la lista de IDs actuales
        lista_ids = [item['id'] for item in st.session_state.inventario]
        
        if lista_ids:
            id_a_borrar = st.selectbox("Seleccionar ID:", lista_ids)
            
            # Botón con tipo 'primary' (rojo en algunos temas) para destacar peligro
            if st.button("🗑️ Borrar Definitivamente", type="primary"):
                # Filtramos la lista para quitar el elemento seleccionado
                st.session_state.inventario = [
                    item for item in st.session_state.inventario 
                    if item['id'] != id_a_borrar
                ]
                # Guardamos la nueva lista (ya sin el elemento)
                guardar_datos(st.session_state.inventario)
                st.success(f"Se ha eliminado '{id_a_borrar}' del sistema.")
                st.rerun()
        else:
            st.info("No hay nada que borrar por ahora.")

# --- CUERPO PRINCIPAL: BUSCADOR Y TABLA ---

col1, col2 = st.columns([3, 1])
with col1:
    busqueda = st.text_input("🔍 Buscar objeto", placeholder="Escribe qué buscas...")
with col2:
    st.metric(label="Total de Bultos", value=len(st.session_state.inventario))

st.divider()

if len(st.session_state.inventario) > 0:
    df = pd.DataFrame(st.session_state.inventario)
    df.columns = ["ID", "Tipo", "Contenido", "Ubicación"]

    if busqueda:
        filtro = df[
            df['Contenido'].str.contains(busqueda, case=False, na=False) | 
            df['ID'].str.contains(busqueda, case=False, na=False)
        ]
        if not filtro.empty:
            st.success(f"Resultados encontrados: {len(filtro)}")
            st.dataframe(filtro, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No se encontró nada con '{busqueda}'.")
    else:
        st.subheader("📋 Inventario Completo")
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("El inventario está vacío. Usa el panel izquierdo para comenzar.")
