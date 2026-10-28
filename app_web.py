"""
Calculadora de derivadas (versión web con Streamlit).

Reutiliza todo el cálculo de derivadas.py: derivada, segunda derivada,
puntos críticos, procedimiento paso a paso, gráfica y PDF.

Para probarla en tu computadora:
    pip install -r requirements.txt
    streamlit run app_web.py
"""

import io

import streamlit as st
import sympy as sp
from matplotlib.figure import Figure

import derivadas as d

MAX_CARACTERES = 80

EJEMPLOS = [
    "x^3 - 3x",
    "x^2*sen(x)",
    "exp(x)/x",
    "ln(x^2 + 1)",
    "(x^2 + 1)^3",
    "raiz(x)*cos(x)",
]

st.set_page_config(page_title="Calculadora de derivadas", page_icon="📈")


# ----------------------------------------------------------------------------
# Cálculo (con caché para no repetir trabajo)
# ----------------------------------------------------------------------------

@st.cache_data(show_spinner=False, max_entries=200)
def calcular(texto):
    expr = d.leer_funcion(texto)
    resumen, proc, deriv, deriv2 = d.construir_informe(expr)
    return expr, resumen, proc, deriv, deriv2


@st.cache_data(show_spinner=False, max_entries=50)
def generar_pdf(texto):
    expr = d.leer_funcion(texto)
    buffer = io.BytesIO()
    d.exportar_pdf(buffer, expr)
    return buffer.getvalue()


def latex(expr):
    try:
        return sp.latex(expr)
    except Exception:
        return d.como_texto(expr)


# ----------------------------------------------------------------------------
# Procedimiento en pantalla
# ----------------------------------------------------------------------------

def mostrar_procedimiento(proc):
    """Muestra cada paso con su título y su explicación."""
    bloques = []
    respuesta = None
    actual = None
    for nivel, linea in proc:
        if linea.startswith("Paso "):
            actual = [linea, []]
            bloques.append(actual)
        elif linea.startswith("Respuesta"):
            respuesta = linea
            actual = None
        elif linea and actual is not None:
            actual[1].append("    " * max(nivel - 1, 0) + linea)

    for titulo, cuerpo in bloques:
        st.markdown(f"**{titulo}**")
        st.code("\n".join(cuerpo), language="text")
    if respuesta:
        st.success(respuesta)


# ----------------------------------------------------------------------------
# Pantalla
# ----------------------------------------------------------------------------

st.title("📈 Calculadora de derivadas")
st.write(
    "Escribe una función de x y obtén su derivada, el procedimiento paso a paso, "
    "la gráfica y un PDF para descargar."
)

if "funcion" not in st.session_state:
    st.session_state["funcion"] = EJEMPLOS[0]


def poner_ejemplo(ejemplo):
    st.session_state["funcion"] = ejemplo


texto = st.text_input(
    "f(x) =", key="funcion", max_chars=MAX_CARACTERES,
    help="Puedes escribir 2x en lugar de 2*x, y x^2 para elevar al cuadrado.",
)

st.caption("Prueba con un ejemplo:")
columnas = st.columns(3)
for i, ejemplo in enumerate(EJEMPLOS):
    columnas[i % 3].button(
        ejemplo, key=f"ej_{i}", on_click=poner_ejemplo, args=(ejemplo,),
        use_container_width=True,
    )

with st.expander("¿Qué puedo escribir?"):
    st.markdown(
        """
- Suma, resta, producto y división: `x^2 + 3x`, `x*sen(x)`, `(x+1)/(x^2+1)`
- Potencias y raíces: `x^3`, `raiz(x)`, `x^(1/3)`
- Trigonométricas: `sen(x)`, `cos(x)`, `tg(x)`
- Inversas: `arcsen(x)`, `arccos(x)`, `arctan(x)`
- Exponenciales y logaritmos: `exp(x)`, `e^x`, `2^x`, `ln(x)`
- Solo se permite la variable **x**.
        """
    )

if not texto.strip():
    st.info("Escribe una función para empezar.")
    st.stop()

try:
    expr, resumen, proc, deriv, deriv2 = calcular(texto)
except ValueError as error:
    st.error(str(error))
    st.stop()
except Exception:
    st.error("No pude derivar esa función. Prueba con otra expresión.")
    st.stop()

# Resultado
st.subheader("Resultado")
st.latex("f(x) = " + latex(expr))
st.latex("f'(x) = " + latex(deriv))
st.latex("f''(x) = " + latex(deriv2))

# Gráfica
st.subheader("Gráfica")
fig = Figure(figsize=(8, 4.5))
d.dibujar(fig, expr, deriv)
st.pyplot(fig)
st.caption("Azul: f(x).  Rojo: f'(x).")

# Puntos críticos
st.subheader("Puntos críticos")
lineas = [("    " * n) + s for n, s in resumen[5:]]
st.code("\n".join(lineas) or "Sin datos", language="text")

# Procedimiento
st.subheader("Procedimiento paso a paso")
mostrar_procedimiento(proc)

# PDF
st.subheader("Descargar")
try:
    st.download_button(
        "📄 Descargar PDF con resultado, gráfica y procedimiento",
        data=generar_pdf(texto),
        file_name="derivada.pdf",
        mime="application/pdf",
    )
except Exception:
    st.warning("No se pudo generar el PDF para esta función.")
