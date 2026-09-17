# ACT-015 — Legibilidad del chat, pantallas de carga y una sola vista de mapa

| Campo | Valor |
|---|---|
| Fecha | 2026-09-17 |
| Versión | 2.4.0 |
| Tipo | corrección + funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

Sobre la versión anterior, el equipo pidió cinco cosas: que las letras del chat
se lean, que el botón del chat se vea como botón y no como un mensaje, que el
ícono de quien pregunta sea blanco, que en la vista de desarrollo se muestre
**solo** el mapa en el que se está trabajando, y las dos pantallas de carga de
la maqueta (la portada "U-BÍCATE" y la bienvenida).

## Qué se hizo

### El texto del chat no se leía: era azul sobre azul

El reporte ("las letras no se notan bien") tenía una causa concreta, que se
encontró **midiendo el color aplicado en el navegador**, no mirando el CSS: el
texto del asistente salía en `#2C3E5C` sobre un fondo `#7391B5`, **1,9:1 de
contraste**. La regla que pinta de azul oscuro el texto dentro de las tarjetas
blancas le ganaba a la de la burbuja, porque la burbuja vive dentro de la
tarjeta.

Dos arreglos:

- la regla de la burbuja lleva `!important`, con el motivo escrito al lado;
- la burbuja pasa de `#7391B5` a **`#3F5C86`** (`AZUL_BURBUJA`). El azul de la
  maqueta deja el texto blanco en 3,3:1, bajo el mínimo accesible de 4,5:1;
  el nuevo llega a **6,8:1** sin salirse de la familia de color.

Comprobado en el navegador: `texto=rgb(255,255,255)` sobre `rgb(63,92,134)`.

También se arreglaron, en la misma burbuja, los **enlaces** (salían celestes
sobre azul, ilegibles) y el desplegable **"De dónde saqué esto"**.

### El botón del chat parecía un mensaje

Era una pastilla roja ancha con la imagen a la izquierda y el texto alineado a
la izquierda: la misma forma que una burbuja. Ahora tiene texto centrado, en
versaditas, y un borde inferior sólido que se hunde al pulsarlo.

### Ícono de quien pregunta

El emoji 🧑‍🎓 se veía como un cuadro oscuro. Se reemplazó por una **silueta
blanca** sobre un círculo azul, dibujada como SVG en `tema.py`. Es un ícono
genérico de interfaz, no arte del equipo, así que se dibuja acá y no se pide
como archivo.

### Un solo mapa por versión

`panel_mapa.py` — en la versión de desarrollo se muestra **solo el plano
interior**, que es lo que se está construyendo; en la estable, solo el mapa del
campus. Nunca los dos. Antes el plano interior estaba en un desplegable bajo el
mapa del campus.

Si en desarrollo el destino no tiene plano levantado (cualquier cosa que no sea
el piso -1 del 851), se explica eso en vez de mostrar el otro mapa.

### Pantallas de carga

`ui/componentes/pantalla_carga.py` — la **portada** (chincheta + "U-BÍCATE")
antes de pedir la clave, y la **bienvenida** (mascota + "¡BIENVENIDO!") apenas
se entra. Cada una una vez por sesión.

**Cómo se hizo, y por qué no con `time.sleep`:** la primera versión dibujaba la
pantalla, esperaba y recargaba. Al verlo en el navegador aparecieron dos
problemas: bloquea la sesión, y Streamlit deja a la vista —en gris— lo de la
pasada anterior hasta que la nueva termina, así que **el formulario de acceso
se veía por debajo de la bienvenida** durante los dos segundos. La versión que
quedó es una capa fija que se desvanece sola con una animación de CSS: no
bloquea nada y la aplicación carga por detrás, que es lo que se espera de una
pantalla de carga.

### La mascota

El equipo copió `assets/mascota.png` y `assets/mascota_cuerpo.png` durante esta
entrega. Ya aparecen: la cara como avatar del asistente y dentro del botón del
chat, el cuerpo entero en la bienvenida.

## Cómo se probó

Con la aplicación levantada y el navegador:

- **Contraste medido**, no estimado: color del texto y del fondo leídos del
  navegador y calculada la razón.
- Portada → acceso → bienvenida → aplicación, comprobando en cada paso que la
  anterior ya no se ve.
- Versión desarrollo con B04: aparece el plano interior y **no** el mapa del
  campus (se verifica por su leyenda).
- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 63 ok.
- `ruff check src tests scripts`: limpio.
- `python scripts/validar_datos.py`: 0 errores, 0 avisos.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | En la versión de desarrollo ya no está el mapa del campus. Es lo pedido |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

`assets/mascota.png` y `assets/mascota_cuerpo.png` tienen que viajar con el
repositorio. Sin ellas la aplicación funciona igual, pero sin mascota.

## Qué quedó pendiente

- **Pantalla de registro** (maqueta, láminas 4 y 5): depende de que haya
  cuentas de verdad (ADR-0010).
- **Menú y avatar en la cabecera** de la maqueta: hoy son la barra lateral de
  Streamlit y la sesión con clave compartida.
- **`tests/test_proveedores.py` sigue roto en `main`**, de antes de esta
  entrega; bloquea `make ci` completo.
