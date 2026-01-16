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
            return [] # Si el archivo está dañado, regresa lista vacía
    return [] # Si no existe, regresa lista vacía

def guardar_datos(lista_inventario):
    """Guarda la lista de diccionarios en el archivo JSON."""
    with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
        json.dump(lista_inventario, f, indent=4, ensure_ascii=False)

# Configuración de página
st.set_page_config(page_title="Inventario Permanente", layout="wide", page_icon="📦")
st.title("📦 Inventario de Bodega (Guardado Automático)")

# --- CARGAR DATOS AL INICIO ---
# Usamos session_state para manejar la interfaz, pero la fuente de verdad es el JSON
if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_datos()

# --- BARRA LATERAL: AGREGAR ---
with st.sidebar:
    st.header("➕ Agregar Contenedor")
    
    # Formulario para agregar datos
    with st.form("nuevo_item", clear_on_submit=True):
        id_input = st.text_input("ID Único (Ej: CAJA-01)", placeholder="Escribe el ID aquí...")
        tipo_input = st.selectbox("Tipo", ["Caja", "Bolsa", "Maleta", "Mueble", "Otro"])
        contenido_input = st.text_area("Contenido", placeholder="Ej: Adornos de navidad, luces, esferas...")
        ubicacion_input = st.text_input("Ubicación", placeholder="Ej: Estante 1, repisa de arriba")
        
        enviar = st.form_submit_button("💾 Guardar en Inventario")
        
        if enviar:
            if id_input and contenido_input:
                # 1. Verificar si el ID ya existe para no duplicar
                ids_existentes = [item['id'] for item in st.session_state.inventario]
                
                if id_input in ids_existentes:
                    st.error(f"¡Error! El ID '{id_input}' ya existe. Usa otro.")
                else:
                    # 2. Crear el diccionario del nuevo item
                    nuevo_item = {
                        "id": id_input,
                        "tipo": tipo_input,
                        "contenido": contenido_input,
                        "ubicacion": ubicacion_input
                    }
                    
                    # 3. Agregar a la lista y GUARDAR en archivo
                    st.session_state.inventario.append(nuevo_item)
                    guardar_datos(st.session_state.inventario) # <--- Aquí ocurre la magia del guardado permanente
                    st.success(f"¡{id_input} guardado correctamente!")
            else:
                st.warning("El ID y el Contenido son obligatorios.")

# --- CUERPO PRINCIPAL: BUSCADOR Y TABLA ---

col1, col2 = st.columns([3, 1])
with col1:
    busqueda = st.text_input("🔍 Buscar objeto (Ej: 'luces')", placeholder="Escribe qué buscas...")
with col2:
    st.write("") # Espacio
    st.write(f"**Total de bultos:** {len(st.session_state.inventario)}")

st.divider()

if len(st.session_state.inventario) > 0:
    # Convertimos la lista de diccionarios a DataFrame para visualizar mejor y filtrar
    df = pd.DataFrame(st.session_state.inventario)
    
    # Renombrar columnas para que se vea bonito en la tabla
    df.columns = ["ID", "Tipo", "Contenido", "Ubicación"]

    if busqueda:
        # Filtro inteligente: busca en contenido O en ID
        filtro = df[
            df['Contenido'].str.contains(busqueda, case=False, na=False) | 
            df['ID'].str.contains(busqueda, case=False, na=False)
        ]
        
        if not filtro.empty:
            st.success(f"Se encontraron {len(filtro)} resultados:")
            st.dataframe(filtro, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No se encontró nada con '{busqueda}'.")
    else:
        st.subheader("📋 Todo el Inventario")
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("El inventario está vacío. Comienza agregando cajas en el menú de la izquierda.")
