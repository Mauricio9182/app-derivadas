"""
Derivadas: calculadora de derivadas con gráfica, procedimiento y PDF.
 
Escribes una función de x, el programa calcula su derivada (y la segunda
derivada) de forma simbólica, muestra el procedimiento paso a paso, dibuja
las curvas y puede guardar todo en un PDF.
 
Instalación (una sola vez):
    pip install sympy matplotlib numpy
 
Uso:
    python derivadas.py
 
Ejemplos de funciones que entiende:
    x^3 - 3x        (puedes escribir 2x en lugar de 2*x)
    x^2*sen(x)
    exp(x)/x
    raiz(x)*cos(x)
    ln(x^2 + 1)
    arctan(x), tg(x), arcsen(x)
"""
 
import re
import textwrap
 
import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages
 
x = sp.Symbol("x")
 
# Permite escribir x^2 (en vez de x**2) y 2x (en vez de 2*x).
TRANSFORMACIONES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
 
# Nombres extra que se aceptan además de los de sympy.
NOMBRES = {
    "x": x, "e": sp.E, "pi": sp.pi,
    "sen": sp.sin, "tg": sp.tan, "ln": sp.log, "raiz": sp.sqrt,
    "arcsen": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
}
 
 
# ----------------------------------------------------------------------------
# Cálculo
# ----------------------------------------------------------------------------
 
def leer_funcion(texto):
    """Convierte el texto escrito por el usuario en una expresión de sympy."""
    texto = texto.strip()
    if not texto:
        raise ValueError("Escribe una función de x, por ejemplo x^2 + 3x.")
    try:
        expr = parse_expr(texto, local_dict=NOMBRES, transformations=TRANSFORMACIONES)
    except Exception:
        raise ValueError(
            "No entendí esa expresión. Revisa los paréntesis y los nombres "
            "de las funciones (sen, cos, tg, exp, ln, raiz, arcsen, arccos, arctan)."
        )
    if not isinstance(expr, sp.Expr):
        raise ValueError("Escribe una función de x, por ejemplo x^2 + 3x.")
    if not expr.free_symbols <= {x}:
        raise ValueError("La función solo puede usar la variable x.")
    return expr
 
 
def derivar(expr):
    """Derivada de expr respecto a x, simplificada."""
    return sp.simplify(sp.diff(expr, x))
 
 
# Nombres que sympy escribe en inglés y que se muestran en español.
NOMBRES_ES = {
    "asin": "arcsen", "acos": "arccos", "atan": "arctan",
    "sin": "sen", "tan": "tg", "log": "ln", "sqrt": "raiz",
}
 
 
def como_texto(expr):
    """Expresión de sympy en un texto fácil de leer (x^2 en vez de x**2)."""
    texto = sp.sstr(expr).replace("**", "^")
    for ingles, espanol in NOMBRES_ES.items():
        texto = re.sub(rf"\b{ingles}\(", f"{espanol}(", texto)
    return texto
 
 
def evaluar(expr, xs):
    """Evalúa expr en un arreglo de valores; lo que no existe queda como NaN."""
    f = sp.lambdify(x, expr, modules="numpy")
    with np.errstate(all="ignore"):
        ys = np.array(f(xs), dtype=complex)
    ys = np.where(np.abs(ys.imag) < 1e-12, ys.real, np.nan)
    ys = np.broadcast_to(ys, xs.shape).astype(float)
    ys[~np.isfinite(ys)] = np.nan
    return ys
 
 
# ----------------------------------------------------------------------------
# Gráfica
# ----------------------------------------------------------------------------
 
def dibujar(fig, expr, deriv, xmin=-10.0, xmax=10.0, ejes=None):
    """Dibuja f(x) y f'(x) en la figura de matplotlib."""
    xs = np.linspace(xmin, xmax, 2000)
    y_f = evaluar(expr, xs)
    y_d = evaluar(deriv, xs)
 
    # Escala vertical: ignora valores extremos (por ejemplo cerca de una asíntota).
    validos = np.concatenate([y_f[np.isfinite(y_f)], y_d[np.isfinite(y_d)]])
    if validos.size:
        bajo, alto = np.percentile(validos, [3, 97])
        bajo, alto = min(bajo, 0), max(alto, 0)
        margen = (alto - bajo) * 0.15 or 1.0
        bajo, alto = bajo - margen, alto + margen
    else:
        bajo, alto = -5.0, 5.0
 
    # Corta la línea donde la curva salta de un lado a otro (asíntotas).
    for ys in (y_f, y_d):
        saltos = np.abs(np.diff(ys)) > (alto - bajo) * 2
        ys[1:][saltos] = np.nan
 
    if ejes is None:
        fig.clear()
        ax = fig.add_subplot(111)
    else:
        ax = ejes
    ax.plot(xs, y_f, color="#1f4fd8", linewidth=2.4, label="f(x)")
    ax.plot(xs, y_d, color="#d62f2f", linewidth=2.0, label="f'(x)")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(bajo, alto)
    ax.grid(True, color="#dde3ea", linewidth=0.8)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.axvline(0, color="#222222", linewidth=1)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(loc="upper right", frameon=False)
    if ejes is None:
        fig.tight_layout()
 
 
# ----------------------------------------------------------------------------
# Procedimiento paso a paso
# ----------------------------------------------------------------------------
 
def es_simple(e):
    """True si la derivada de e se obtiene directo, sin pasos intermedios."""
    if not e.has(x) or e == x:
        return True
    if e.is_Pow and e.base == x and not e.exp.has(x):
        return True
    if isinstance(e, sp.Function) and len(e.args) == 1 and e.args[0] == x:
        return True
    if e.is_Mul:
        k, resto = e.as_independent(x, as_Add=False)
        return k != 1 and es_simple(resto)
    return False
 
 
def motivo(e):
    """Frase corta que explica por qué la derivada simple es esa."""
    if not e.has(x):
        return "es un número, su derivada es 0"
    if e == x:
        return "la derivada de x es 1"
    if e.is_Pow:
        return "regla de la potencia"
    if isinstance(e, sp.Function):
        return "derivada que se memoriza"
    return "el número se queda y se deriva el resto"
 
 
def sub(etiqueta, e, nivel):
    """Derivada de una parte de la función: en una línea si es fácil, o con pasos."""
    if es_simple(e):
        return [(nivel, f"{etiqueta} = {como_texto(sp.diff(e, x))}   ({motivo(e)})")]
    return [(nivel, f"Para calcular {etiqueta}:")] + explicar(e, nivel + 1)
 
 
def explicar(e, nivel=0):
    """Lista de (nivel, texto) que explica cómo se deriva e, en lenguaje sencillo."""
    t = como_texto
    L = []
 
    def add(texto):
        L.append((nivel, texto))
 
    d = sp.diff(e, x)
    res = t(d)
 
    if not e.has(x):
        add(f"{t(e)} es un número (constante): su derivada es 0.")
 
    elif e == x:
        add("La derivada de x es 1.")
 
    elif e.is_Add:
        add("Es una suma: se deriva cada término por separado y luego se suman.")
        for termino in e.args:
            L += sub(f"d/dx[{t(termino)}]", termino, nivel + 1)
        add(f"Se suman los resultados: {res}")
 
    elif e.is_Mul:
        k, resto = e.as_independent(x, as_Add=False)
        num, den = sp.fraction(e)
        if k != 1:
            add(f"El número {t(k)} está multiplicando: se queda igual y solo se deriva {t(resto)}.")
            L += sub(f"d/dx[{t(resto)}]", resto, nivel + 1)
            add(f"Se multiplica: {t(k)} · ({t(sp.diff(resto, x))}) = {res}")
        elif den.has(x):
            u, v = num, den
            add("Es una división. Se usa la regla del cociente:")
            add("(u/v)' = (u'·v − u·v') / v²")
            add(f"Aquí  u = {t(u)}   y   v = {t(v)}")
            L += sub("u'", u, nivel + 1)
            L += sub("v'", v, nivel + 1)
            du, dv = sp.diff(u, x), sp.diff(v, x)
            add(f"Se sustituye: (({t(du)})·({t(v)}) − ({t(u)})·({t(dv)})) / ({t(v)})^2")
            add(f"Resultado: {res}")
        else:
            u = e.args[0]
            v = sp.Mul(*e.args[1:])
            add("Es una multiplicación de dos partes. Se usa la regla del producto:")
            add("(u·v)' = u'·v + u·v'")
            add(f"Aquí  u = {t(u)}   y   v = {t(v)}")
            L += sub("u'", u, nivel + 1)
            L += sub("v'", v, nivel + 1)
            du, dv = sp.diff(u, x), sp.diff(v, x)
            add(f"Se sustituye: ({t(du)})·({t(v)}) + ({t(u)})·({t(dv)})")
            add(f"Resultado: {res}")
 
    elif e.is_Pow:
        base, ex = e.as_base_exp()
        if not ex.has(x):
            n = t(ex)
            if base == x:
                add("Regla de la potencia: el exponente baja a multiplicar y al exponente se le resta 1.")
                add(f"d/dx[x^n] = n·x^(n − 1)   con n = {n}")
                add(f"Resultado: {n}·x^({n} − 1) = {res}")
            else:
                add("Es una potencia de algo más complicado que x. Se usa la regla de la cadena:")
                add("d/dx[u^n] = n·u^(n − 1)·u'")
                add(f"Aquí  u = {t(base)}   y   n = {n}")
                L += sub("u'", base, nivel + 1)
                add(f"Se sustituye: {n}·({t(base)})^({n} − 1)·({t(sp.diff(base, x))})")
                add(f"Resultado: {res}")
        elif not base.has(x):
            add("Un número elevado a una expresión con x. Regla: d/dx[a^u] = a^u·ln(a)·u'")
            add(f"Aquí  a = {t(base)}   y   u = {t(ex)}")
            L += sub("u'", ex, nivel + 1)
            add(f"Resultado: {res}")
        else:
            add("La x está en la base y en el exponente: se resuelve con derivación logarítmica.")
            add(f"Resultado: {res}")
 
    elif isinstance(e, sp.Function) and len(e.args) == 1:
        u = e.args[0]
        w = sp.Symbol("u")
        afuera = sp.diff(e.func(w), w)
        if u == x:
            add("Esta es una derivada básica que se memoriza (está en la tabla de derivadas):")
            add(f"d/dx[{t(e)}] = {res}")
        else:
            add("Hay una función dentro de otra. Se usa la regla de la cadena:")
            add("se deriva la de afuera (sin tocar lo de adentro) y se multiplica por la derivada de lo de adentro.")
            add(f"Adentro:  u = {t(u)}")
            add(f"Afuera:  {t(e.func(w))}  →  su derivada es  {t(afuera)}")
            L += sub("u'", u, nivel + 1)
            add(f"Se multiplica: ({t(afuera.subs(w, u))})·({t(sp.diff(u, x))})")
            add(f"Resultado: {res}")
 
    else:
        add(f"Resultado: {res}")
 
    return L
 
 
def construir_procedimiento(expr, deriv):
    """Procedimiento completo, numerado, como lista de (nivel, texto)."""
    t = como_texto
    L = [(0, f"Función: f(x) = {t(expr)}"), (0, "")]
    contador = [0]
 
    def paso(titulo):
        contador[0] += 1
        L.append((0, f"Paso {contador[0]}. {titulo}"))
 
    terminos = list(expr.args) if expr.is_Add else [expr]
    varios = len(terminos) > 1
 
    if varios:
        paso("Separar la función en términos")
        L.append((1, f"Hay {len(terminos)} términos:  " + ",  ".join(t(a) for a in terminos)))
        L.append((1, "Cada término se deriva por separado y al final se suman los resultados."))
        L.append((0, ""))
 
    ders = []
    for termino in terminos:
        paso(f"Derivar el término  {t(termino)}" if varios else f"Derivar  {t(termino)}")
        L += explicar(termino, 1)
        ders.append(sp.diff(termino, x))
        L.append((0, ""))
 
    bruto = sp.diff(expr, x)
    if varios:
        paso("Sumar las derivadas de cada término")
        L.append((1, " + ".join(f"({t(d)})" for d in ders) + f"  =  {t(bruto)}"))
        L.append((0, ""))
    if t(bruto) != t(deriv):
        paso("Simplificar")
        L.append((1, f"{t(bruto)}  =  {t(deriv)}"))
        L.append((0, ""))
 
    L.append((0, f"Respuesta: f'(x) = {t(deriv)}"))
    return L
 
 
# ----------------------------------------------------------------------------
# Puntos críticos e informe
# ----------------------------------------------------------------------------
 
def puntos_criticos(expr, deriv, deriv2):
    """Puntos donde f'(x) = 0, clasificados con la segunda derivada."""
    try:
        soluciones = sp.solve(sp.Eq(deriv, 0), x)
    except Exception:
        return None
    filas = []
    for s in soluciones:
        try:
            xv = float(s)
            yv = float(expr.subs(x, s))
            c = float(deriv2.subs(x, s))
        except (TypeError, ValueError):
            continue  # soluciones complejas o fuera del dominio
        if c > 1e-9:
            tipo = "mínimo local"
        elif c < -1e-9:
            tipo = "máximo local"
        else:
            tipo = "no concluyente (f'' = 0)"
        filas.append((xv, yv, tipo))
    return sorted(filas)[:10]
 
 
def construir_informe(expr):
    """Devuelve (resumen, procedimiento, deriv, deriv2).
 
    resumen y procedimiento son listas de (nivel, texto)."""
    deriv = derivar(expr)
    deriv2 = derivar(deriv)
    resumen = [
        (0, f"f(x)   = {como_texto(expr)}"),
        (0, f"f'(x)  = {como_texto(deriv)}"),
        (0, f"f''(x) = {como_texto(deriv2)}"),
        (0, ""),
        (0, "Puntos críticos (f'(x) = 0):"),
    ]
    filas = puntos_criticos(expr, deriv, deriv2)
    if filas is None:
        resumen.append((1, "No se pudieron calcular de forma exacta."))
    elif not filas:
        resumen.append((1, "No hay puntos reales con f'(x) = 0."))
    else:
        for xv, yv, tipo in filas:
            resumen.append((1, f"x = {xv:.4f},  f(x) = {yv:.4f}  ->  {tipo}"))
 
    proc = construir_procedimiento(expr, deriv)
    return resumen, proc, deriv, deriv2
 
 
def lineas_envueltas(lineas, ancho=88):
    """Convierte (nivel, texto) en líneas de texto que caben en la página."""
    salida = []
    for nivel, texto in lineas:
        sangria = "    " * nivel
        salida += textwrap.wrap(
            texto, ancho, initial_indent=sangria,
            subsequent_indent=sangria + "   ",
        ) or [""]
    return salida
 
 
# ----------------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------------
 
def exportar_pdf(ruta, expr):
    """Guarda un PDF: resultado + gráfica (página 1) y procedimiento (siguientes)."""
    resumen, proc, deriv, _ = construir_informe(expr)
    A4 = (8.27, 11.69)
    paso = 0.0185
 
    with PdfPages(ruta) as pdf:
        # Página 1: resultado y gráfica
        fig = Figure(figsize=A4)
        fig.text(0.08, 0.95, "Calculadora de derivadas", fontsize=16, weight="bold")
        y = 0.91
        for linea in lineas_envueltas(resumen):
            fig.text(0.08, y, linea, family="monospace", fontsize=9.5)
            y -= paso
        ejes = fig.add_axes([0.1, 0.07, 0.82, 0.38])
        dibujar(fig, expr, deriv, ejes=ejes)
        pdf.savefig(fig)
 
        # Páginas siguientes: procedimiento
        lineas = lineas_envueltas(proc)
        por_pagina = 48
        for i in range(0, len(lineas), por_pagina):
            fig = Figure(figsize=A4)
            if i == 0:
                fig.text(0.08, 0.95, "Procedimiento paso a paso",
                         fontsize=14, weight="bold")
            y = 0.91
            for linea in lineas[i:i + por_pagina]:
                negrita = linea.startswith(("Paso ", "Respuesta"))
                fig.text(0.08, y, linea, family="monospace", fontsize=9,
                         weight="bold" if negrita else "normal")
                y -= paso
            pdf.savefig(fig)
 
 
# ----------------------------------------------------------------------------
# Ventana
# ----------------------------------------------------------------------------
 
def abrir_ventana():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg,
        NavigationToolbar2Tk,
    )
 
    TRADUCCION = {
        "home": ("Inicio", "Restablecer la vista original"),
        "back": ("Atrás", "Volver a la vista anterior"),
        "forward": ("Adelante", "Ir a la vista siguiente"),
        "pan": ("Mover", "Clic izquierdo mueve, clic derecho hace zoom\n"
                         "x/y fija el eje, CTRL fija la proporción"),
        "zoom": ("Zoom", "Hacer zoom con un rectángulo\nx/y fija el eje"),
        "configure_subplots": ("Márgenes", "Configurar márgenes de la gráfica"),
        "save_figure": ("Guardar", "Guardar la gráfica como imagen"),
    }
 
    class BarraHerramientas(NavigationToolbar2Tk):
        toolitems = tuple(
            (TRADUCCION[cb][0], TRADUCCION[cb][1], img, cb)
            if cb in TRADUCCION else (nombre, tip, img, cb)
            for nombre, tip, img, cb in NavigationToolbar2Tk.toolitems
        )
 
    ventana = tk.Tk()
    ventana.title("Derivadas")
    ventana.geometry("900x720")
    ventana.minsize(560, 480)
 
    # Fila de entrada
    arriba = ttk.Frame(ventana, padding=(14, 14, 14, 6))
    arriba.pack(fill="x")
    ttk.Label(arriba, text="f(x) =", font=("Consolas", 15)).pack(side="left")
    entrada = ttk.Entry(arriba, font=("Consolas", 15))
    entrada.pack(side="left", fill="x", expand=True, padx=10)
    entrada.insert(0, "x^3 - 3x")
    entrada.focus()
 
    # Resultado y errores
    resultado = tk.StringVar()
    mensaje_error = tk.StringVar()
    ttk.Label(
        ventana, textvariable=resultado, font=("Consolas", 13),
        foreground="#d62f2f", padding=(14, 4)
    ).pack(fill="x")
    ttk.Label(
        ventana, textvariable=mensaje_error,
        foreground="#a3261b", padding=(14, 0)
    ).pack(fill="x")
 
    # Pestañas: gráfica y procedimiento
    pestanas = ttk.Notebook(ventana)
    pestanas.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    tab_grafica = ttk.Frame(pestanas)
    tab_proc = ttk.Frame(pestanas)
    pestanas.add(tab_grafica, text="Gráfica")
    pestanas.add(tab_proc, text="Procedimiento")
 
    fig = Figure(figsize=(8, 5), dpi=100)
    lienzo = FigureCanvasTkAgg(fig, master=tab_grafica)
    BarraHerramientas(lienzo, tab_grafica, pack_toolbar=True)
    lienzo.get_tk_widget().pack(fill="both", expand=True)
 
    texto = tk.Text(tab_proc, font=("Consolas", 12), wrap="word",
                    state="disabled", padx=10, pady=10)
    texto.tag_configure("titulo", font=("Consolas", 12, "bold"),
                        foreground="#1f4fd8", spacing1=4)
    barra = ttk.Scrollbar(tab_proc, command=texto.yview)
    texto.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    texto.pack(fill="both", expand=True)
 
    actual = {"expr": None}
 
    def graficar(_evento=None):
        try:
            expr = leer_funcion(entrada.get())
            resumen, proc, deriv, deriv2 = construir_informe(expr)
        except ValueError as error:
            mensaje_error.set(str(error))
            return
        except Exception:
            mensaje_error.set("No pude derivar esa función. Prueba con otra expresión.")
            return
        mensaje_error.set("")
        actual["expr"] = expr
        resultado.set(
            "f'(x)  = " + como_texto(deriv) + "\nf''(x) = " + como_texto(deriv2)
        )
        dibujar(fig, expr, deriv)
        lienzo.draw()
 
        # Procedimiento en la pestaña
        lineas = resumen[3:] + [(0, ""), (0, "PROCEDIMIENTO"), (0, "")] + proc
        texto.configure(state="normal")
        texto.delete("1.0", "end")
        for n, linea in lineas:
            es_titulo = linea.startswith(("Paso ", "Respuesta", "PROCEDIMIENTO"))
            texto.insert("end", "    " * n + linea + "\n",
                         ("titulo",) if es_titulo else ())
        texto.configure(state="disabled")
 
    def guardar_pdf():
        if actual["expr"] is None:
            mensaje_error.set("Primero grafica una función válida.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile="derivada.pdf",
        )
        if not ruta:
            return
        try:
            exportar_pdf(ruta, actual["expr"])
            messagebox.showinfo("Listo", f"PDF guardado en:\n{ruta}")
        except Exception as error:
            messagebox.showerror("No se pudo guardar el PDF", str(error))
 
    ttk.Button(arriba, text="Graficar", command=graficar).pack(side="left")
    ttk.Button(arriba, text="Guardar PDF", command=guardar_pdf).pack(side="left", padx=(6, 0))
    entrada.bind("<Return>", graficar)
    graficar()
    ventana.mainloop()
 
 
if __name__ == "__main__":
    abrir_ventana()