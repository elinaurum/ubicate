# ACT-013 — Aplicar la identidad visual de la maqueta a toda la aplicación

| Campo | Valor |
|---|---|
| Fecha | 2026-09-17 |
| Versión | 2.2.0 |
| Tipo | funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

El equipo entregó la maqueta completa de la aplicación (presentación del curso
IN5524, grupo 7) y pidió un cambio general basado en su estética, no solo en la
pantalla de acceso que ya seguía esos colores.

## Qué se hizo

- `src/ubicate/ui/tema.py` — **nuevo**. La identidad en un solo lugar: la
  paleta, la chincheta como SVG y el CSS de la aplicación. Antes los colores
  vivían sueltos en `pantalla_acceso.py`; ahora salen de aquí.
- `.streamlit/config.toml` — el tema base de Streamlit con los mismos valores,
  que es lo que usan sus propios controles. Queda anotado en los dos archivos
  que son el mismo dato desde dos lados.
- `src/ubicate/ui/app.py` — cabecera con la chincheta y el nombre, en vez del
  título de texto.
- `src/ubicate/ui/componentes/panel_chat.py` — burbujas: el asistente en azul
  medio, quien pregunta en gris, dentro de una tarjeta blanca.
- `src/ubicate/ui/componentes/panel_mapa.py` — la ficha del destino como
  tarjeta blanca.
- `src/ubicate/ui/componentes/pantalla_acceso.py` — usa la paleta compartida.

**Paleta** (de la maqueta): fondo `#2C3E5C`, marca `#E63329`, secundario
`#7391B5`, tarjetas `#FFFFFF`, burbuja de quien pregunta `#E4E6E9`.

## Por qué así

Dos problemas prácticos de dar estilo a Streamlit, y cómo se resolvieron:

1. **Sus clases CSS cambian con cada versión** (`st-emotion-cache-1iitq1e`).
   Todo el CSS apunta a `data-testid`, que sí es estable. Los testids reales
   se leyeron del HTML de la aplicación corriendo, no de memoria: el primer
   intento apuntaba a `data-baseweb`, que esta versión ya no usa, y el botón
   salía azul.
2. **Streamlit no marca en el HTML qué es qué.** No distingue un mensaje del
   asistente de uno de quien pregunta, ni le pone un identificador propio al
   contenedor con borde. La solución es una marca invisible que pone el propio
   componente (`<span class="ub-rol-…">`, `marca_tarjeta()`) y que el CSS usa
   con `:has()`. Es estable porque es nuestra.

No lleva ADR: es un cambio de piel, no una decisión que condicione la
arquitectura. La regla que sí queda —los colores salen de `tema.py`— está en el
docstring del módulo.

## Cómo se probó

Con la aplicación levantada y el navegador, no revisando el código:

- Pantalla de acceso, conversación (con una pregunta real, para ver las dos
  burbujas) y mapa con B04 buscada.
- Se corrigieron dos errores que solo se vieron en la captura:
  - el contenedor con borde no existía como `stVerticalBlockBorderWrapper` en
    esta versión, así que las tarjetas salían azules;
  - al arreglarlo, el `:has()` calzó también los bloques que envuelven la
    tarjeta y **pintó de blanco la página entera**. Se acotó con la ruta
    completa de hijos directos.
- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 63 ok.
- `ruff check src tests scripts`: limpio.
- `python scripts/validar_datos.py`: 0 errores, 0 avisos.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No: cambia cómo se ve, no qué hace |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

Ninguno especial. `.streamlit/config.toml` viaja con el repositorio.

## Qué quedó pendiente

De la maqueta falta lo que **no es estética** y conviene decidir aparte:

- **La mascota** (el gato con lentes) aparece en la bienvenida, como avatar del
  asistente y como botón para abrir el chat. No está implementada: hace falta
  el archivo de imagen. Hoy el avatar del asistente es un emoji.
- **La navegación de la maqueta** es distinta a la actual: cabecera con menú y
  avatar, el mapa como pantalla principal y el chat abriéndose desde el botón
  de la mascota. Hoy hay un selector "Preguntar / Mapa"
  ([ADR-0006](../decisiones/ADR-0006-navegacion-una-vista-a-la-vez.md)).
  Cambiarlo supera ese ADR y es decisión de producto, no de estilo.
- **Pantallas de la maqueta que no existen**: registro, bienvenida y el
  autocompletado del buscador (la maqueta muestra sugerencias mientras se
  escribe; hoy la desambiguación aparece después de buscar).
- **`tests/test_proveedores.py` sigue roto en `main`**, de antes de esta
  entrega.
