# Calculadora de derivadas

Calculadora de derivadas en español. Escribes una función de x y obtienes:

- La derivada f'(x) y la segunda derivada f''(x)
- Los puntos críticos (máximos y mínimos locales)
- El procedimiento paso a paso (reglas de la suma, potencia, producto, cociente y cadena)
- La gráfica de f(x) y f'(x)
- Un PDF con el resultado, la gráfica y el procedimiento

Hay dos versiones:

| Archivo | Qué es |
|---|---|
| `app_web.py` | Versión web (Streamlit). Se usa desde el navegador. |
| `derivadas.py` | Versión de escritorio (tkinter). También contiene todo el cálculo. |

## Probarla en línea

Enlace de la app: _(pega aquí tu enlace de Streamlit)_

## Ejecutarla en tu computadora

```
pip install -r requirements.txt
streamlit run app_web.py
```

Versión de escritorio:

```
python derivadas.py
```

## Funciones que entiende

| Tipo | Ejemplos |
|---|---|
| Polinomios | `x^3 - 3x`, `3x^2 + 2x - 5` |
| Potencias y raíces | `raiz(x)`, `x^(1/3)`, `1/x` |
| Producto y cociente | `x^2*sen(x)`, `exp(x)/x` |
| Regla de la cadena | `(x^2+1)^3`, `sen(2x)`, `exp(x^2)` |
| Trigonométricas | `sen(x)`, `cos(x)`, `tg(x)` |
| Inversas | `arcsen(x)`, `arccos(x)`, `arctan(x)` |
| Exponenciales y logaritmos | `exp(x)`, `2^x`, `ln(x^2+1)` |

Puedes escribir `2x` en lugar de `2*x` y `x^2` para elevar al cuadrado.

## Limitaciones

- Solo usa la variable `x`.
- No calcula integrales, límites ni derivadas implícitas.
- En funciones periódicas como `sen(x)` se muestran solo algunos puntos críticos.
- La gráfica va de -10 a 10.
