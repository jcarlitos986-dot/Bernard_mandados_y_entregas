import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sistema de Reparto Pro", layout="wide")
DATA_FILE = "pedidos_reparto.csv"
COLUMNAS = ["ID", "Cliente", "Servicio", "Dirección", "Estado"]
SERVICIOS = ["Moto taxi", "Servicio de paquetería", "Mandados"]

def normalizar(df):
    """Asegura que el DataFrame tenga todas las columnas (compatible con CSV antiguos)."""
    if "Servicio" not in df.columns:
        df["Servicio"] = "Sin especificar"
    df["Servicio"] = df["Servicio"].fillna("Sin especificar")
    return df[COLUMNAS]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            return normalizar(pd.read_csv(DATA_FILE))
        except Exception:
            return pd.DataFrame(columns=COLUMNAS)
    return pd.DataFrame(columns=COLUMNAS)

# Cargar datos en el estado de la sesión
if "df" not in st.session_state:
    st.session_state.df = cargar_datos()

st.title("Bernard Mandados y Entregas")

# --- REGISTRO ---
with st.sidebar:
    st.header("📝 Nuevo Pedido")
    with st.form("formulario_envio", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente")
        servicio = st.selectbox("Tipo de Servicio", SERVICIOS)
        direccion = st.text_input("Dirección de Entrega")
        submitted = st.form_submit_button("Guardar Pedido")

        if submitted:
            if cliente.strip() and direccion.strip():
                # Generar ID de forma segura
                if st.session_state.df.empty:
                    nuevo_id = 1
                else:
                    nuevo_id = int(st.session_state.df["ID"].max()) + 1

                nueva_fila = pd.DataFrame({
                    "ID": [nuevo_id],
                    "Cliente": [cliente.strip()],
                    "Servicio": [servicio],
                    "Dirección": [direccion.strip()],
                    "Estado": ["Pendiente"]
                })
                st.session_state.df = pd.concat([st.session_state.df, nueva_fila], ignore_index=True)
                st.session_state.df.to_csv(DATA_FILE, index=False)
                st.success("✅ Pedido registrado correctamente")
            else:
                st.warning("Por favor completa todos los campos")

    # --- RESPALDO ---
    st.divider()
    st.header("💾 Respaldo")
    st.download_button(
        "⬇️ Descargar pedidos (CSV)",
        data=st.session_state.df.to_csv(index=False).encode("utf-8"),
        file_name="pedidos_reparto.csv",
        mime="text/csv",
        use_container_width=True,
    )
    archivo = st.file_uploader("Restaurar desde CSV", type="csv")
    if archivo is not None and st.button("Restaurar respaldo", use_container_width=True):
        try:
            df_nuevo = pd.read_csv(archivo)
            if {"ID", "Cliente", "Dirección", "Estado"}.issubset(df_nuevo.columns):
                st.session_state.df = normalizar(df_nuevo)
                st.session_state.df.to_csv(DATA_FILE, index=False)
                st.success("Respaldo restaurado")
                st.rerun()
            else:
                st.error("El CSV no tiene las columnas esperadas")
        except Exception:
            st.error("No se pudo leer el archivo")

# --- CONTROL DE REPARTIDOR ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📦 Lista de Entregas")
    f1, f2 = st.columns(2)
    estado_filtro = f1.selectbox("Filtrar por estado:", ["Todos", "Pendiente", "Entregado"])
    servicio_filtro = f2.selectbox("Filtrar por servicio:", ["Todos"] + SERVICIOS)

    df_f = st.session_state.df.copy()
    if estado_filtro != "Todos":
        df_f = df_f[df_f["Estado"] == estado_filtro]
    if servicio_filtro != "Todos":
        df_f = df_f[df_f["Servicio"] == servicio_filtro]

    if df_f.empty:
        st.info("No hay pedidos para mostrar")
    else:
        st.dataframe(df_f, use_container_width=True, hide_index=True)

with col2:
    st.header("⚙️ Acciones")

    if st.session_state.df.empty:
        st.info("No hay pedidos registrados")
    else:
        df_act = st.session_state.df
        id_update = st.selectbox(
            "ID del Pedido a actualizar",
            options=df_act["ID"].tolist(),
            format_func=lambda i: (
                f"#{i} · {df_act.loc[df_act['ID'] == i, 'Cliente'].iloc[0]} · "
                f"{df_act.loc[df_act['ID'] == i, 'Servicio'].iloc[0]} "
                f"({df_act.loc[df_act['ID'] == i, 'Estado'].iloc[0]})"
            ),
        )
        estado_actual = df_act.loc[df_act["ID"] == id_update, "Estado"].iloc[0]
        opciones = ["Pendiente", "Entregado"]
        nuevo_estado = st.radio(
            "Cambiar estado a:",
            opciones,
            index=1 - opciones.index(estado_actual),
            key=f"radio_estado_{id_update}_{estado_actual}",
        )

        if st.button("Actualizar Estado", type="primary"):
            st.session_state.df.loc[st.session_state.df["ID"] == id_update, "Estado"] = nuevo_estado
            st.session_state.df.to_csv(DATA_FILE, index=False)
            st.success(f"Pedido #{id_update} actualizado a «{nuevo_estado}»")
            st.rerun()
