import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Bernard Mandados y Entregas", layout="wide")

DATA_FILE = "pedidos_reparto.csv"
COLUMNAS = [
    "ID", "Cliente", "Servicio", "Origen", "Destino",
    "Origen_Lat", "Origen_Lon", "Destino_Lat", "Destino_Lon",
    "Forma de cobro", "Forma de pago", "Estado"
]
SERVICIOS = ["Moto taxi", "Servicio de paquetería", "Mandados"]
OPCIONES_COBRO = ["Efectivo", "Transferencia", "Terminal"]
OPCIONES_PAGO = ["Al recoger", "Al entregar"]

LAT_DEFAULT = 17.8077
LON_DEFAULT = -97.7788

def normalizar(df):
    for col in ["Servicio", "Origen", "Destino", "Forma de cobro", "Forma de pago"]:
        if col not in df.columns:
            df[col] = "Sin especificar"
        else:
            df[col] = df[col].fillna("Sin especificar")
            
    for col, default_val in [
        ("Origen_Lat", LAT_DEFAULT), ("Origen_Lon", LON_DEFAULT),
        ("Destino_Lat", LAT_DEFAULT), ("Destino_Lon", LON_DEFAULT)
    ]:
        if col not in df.columns:
            df[col] = default_val
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default_val)
            
    return df[COLUMNAS]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            return normalizar(pd.read_csv(DATA_FILE))
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNAS)

if "df" not in st.session_state:
    st.session_state.df = cargar_datos()

st.title("Bernard Mandados y Entregas")

tab1, tab2, tab3 = st.tabs(["Registrar Pedido", "Lista de Entregas", "Actualizar Estado"])

with tab1:
    st.header("Nuevo Pedido")
    with st.form("formulario_envio", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente")
        servicio = st.selectbox("Tipo de Servicio", SERVICIOS)
        
        col_orig, col_dest = st.columns(2)
        with col_orig:
            origen = st.text_input("Punto de Recogida (Dirección)")
            orig_lat = st.number_input("Latitud Recogida", value=LAT_DEFAULT, format="%.6f")
            orig_lon = st.number_input("Longitud Recogida", value=LON_DEFAULT, format="%.6f")
            
        with col_dest:
            destino = st.text_input("Punto de Destino (Dirección)")
            dest_lat = st.number_input("Latitud Destino", value=LAT_DEFAULT, format="%.6f")
            dest_lon = st.number_input("Longitud Destino", value=LON_DEFAULT, format="%.6f")
            
        cobro = st.selectbox("Forma de Cobro", OPCIONES_COBRO)
        pago = st.selectbox("Forma de Pago", OPCIONES_PAGO)
        submitted = st.form_submit_button("Guardar Pedido")
        
        if submitted:
            if cliente.strip() and origen.strip() and destino.strip():
                if st.session_state.df.empty:
                    nuevo_id = 1
                else:
                    nuevo_id = int(st.session_state.df["ID"].max()) + 1
                
                nueva_fila = pd.DataFrame({
                    "ID": [nuevo_id],
                    "Cliente": [cliente.strip()],
                    "Servicio": [servicio],
                    "Origen": [origen.strip()],
                    "Destino": [destino.strip()],
                    "Origen_Lat": [orig_lat],
                    "Origen_Lon": [orig_lon],
                    "Destino_Lat": [dest_lat],
                    "Destino_Lon": [dest_lon],
                    "Forma de cobro": [cobro],
                    "Forma de pago": [pago],
                    "Estado": ["Pendiente"]
                })
                st.session_state.df = pd.concat([st.session_state.df, nueva_fila], ignore_index=True)
                st.session_state.df.to_csv(DATA_FILE, index=False)
                st.success("Pedido registrado correctamente")
            else:
                st.warning("Por favor completa todos los campos")

with tab2:
    st.header("Lista de Entregas")
    col1, col2 = st.columns(2)
    estado_filtro = col1.selectbox("Filtrar por estado:", ["Todos", "Pendiente", "Entregado"])
    servicio_filtro = col2.selectbox("Filtrar por servicio:", ["Todos"] + SERVICIOS)
    
    df_f = st.session_state.df.copy()
    if estado_filtro != "Todos":
        df_f = df_f[df_f["Estado"] == estado_filtro]
    if servicio_filtro != "Todos":
        df_f = df_f[df_f["Servicio"] == servicio_filtro]
        
    if df_f.empty:
        st.info("No hay pedidos para mostrar")
    else:
        st.dataframe(df_f[["ID", "Cliente", "Servicio", "Origen", "Destino", "Forma de cobro", "Forma de pago", "Estado"]], use_container_width=True, hide_index=True)
        
        st.subheader("Mapa de Ubicaciones")
        mapa_puntos = []
        for idx, row in df_f.iterrows():
            mapa_puntos.append({"lat": row["Origen_Lat"], "lon": row["Origen_Lon"], "Ubicación": f"#{row['ID']} Origen ({row['Cliente']})"})
            mapa_puntos.append({"lat": row["Destino_Lat"], "lon": row["Destino_Lon"], "Ubicación": f"#{row['ID']} Destino ({row['Cliente']})"})
        
        df_mapa = pd.DataFrame(mapa_puntos)
        st.map(df_mapa)

with tab3:
    st.header("Actualizar Estado de Pedido")
    if st.session_state.df.empty:
        st.info("No hay pedidos registrados")
    else:
        id_update = st.selectbox(
            "ID del Pedido a actualizar",
            options=st.session_state.df["ID"].tolist(),
            format_func=lambda i: f"#{i} - {st.session_state.df.loc[st.session_state.df['ID'] == i, 'Cliente'].iloc[0]} ({st.session_state.df.loc[st.session_state.df['ID'] == i, 'Estado'].iloc[0]})"
        )
        estado_actual = st.session_state.df.loc[st.session_state.df["ID"] == id_update, "Estado"].iloc[0]
        opciones = ["Pendiente", "Entregado"]
        nuevo_estado = st.radio("Cambiar estado a:", opciones, index=opciones.index(estado_actual))
        
        if st.button("Actualizar Estado", type="primary"):
            st.session_state.df.loc[st.session_state.df["ID"] == id_update, "Estado"] = nuevo_estado
            st.session_state.df.to_csv(DATA_FILE, index=False)
            st.success(f"Pedido #{id_update} actualizado a '{nuevo_estado}'")
            st.rerun()

st.divider()
st.header("Respaldo de Datos")
st.download_button(
    "Descargar pedidos (CSV)",
    data=st.session_state.df.to_csv(index=False).encode("utf-8"),
    file_name="pedidos_reparto.csv",
    mime="text/csv",
    use_container_width=True
)

archivo = st.file_uploader("Restaurar desde CSV", type="csv")
if archivo is not None and st.button("Restaurar respaldo", use_container_width=True):
    try:
        df_nuevo = pd.read_csv(archivo)
        if set(["ID", "Cliente", "Origen", "Destino", "Forma de cobro", "Forma de pago", "Estado"]).issubset(df_nuevo.columns):
            st.session_state.df = normalizar(df_nuevo)
            st.session_state.df.to_csv(DATA_FILE, index=False)
            st.success("Respaldo restaurado")
            st.rerun()
        else:
            st.error("El CSV no tiene las columnas esperadas")
    except Exception:
        st.error("No se pudo leer el archivo")
