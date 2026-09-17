# ACT-016 — Arreglar las pantallas de carga, mostrar el plano de entrada y dejar `make ci` en verde

| Campo | Valor |
|---|---|
| Fecha | 2026-09-17 |
| Versión | 2.5.0 |
| Tipo | corrección + funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

Cuatro cosas: la pantalla de carga previa al inicio de sesión no funcionaba, la
de bienvenida se veía "bugueada", el plano del 851 debía mostrarse de entrada
sin tener que buscar una sala, y arreglar el error de `test_proveedores`.

## `make ci` pasa completo, por primera vez

`tests/test_proveedores.py` llevaba varias entregas bloqueando la suite. El
diagnóstico inicial —"un import roto"— era incompleto: **la función
`config_pensamiento` nunca existió**, y con ella faltaban dos comportamientos
más que las pruebas ya especificaban. Las pruebas estaban adelantadas a la
implementación.

Lo que faltaba, y se implementó en `chat/proveedores.py`:

1. **`config_pensamiento(settings)`** — cuánto puede razonar el modelo antes de
   contestar. Solo Gemini entiende la opción; a otro endpoint compatible le
   hace rechazar la petición entera. `UBICATE_NIVEL_PENSAMIENTO` ya existía en
   la configuración y estaba documentada, pero **no la usaba nadie**: era un
   ajuste que no hacía nada.
2. **Si el modelo rechaza esa configuración, se sigue sin ella.** Algunos
   modelos de Gemini responden 400 nombrando el campo; antes eso habría dejado
   al usuario sin respuesta por un ajuste opcional. Ahora se apaga para el
   resto de la sesión y se reintenta una vez.
3. **Reintento ante respuesta cortada.** Una respuesta se considera incompleta
   si el proveedor declara una razón distinta de `stop` **o** si el texto no
   cierra (sin punto final ni marca `[[LUGAR:ID]]`): con Gemini llegan
   respuestas cortadas a media frase marcadas como `stop` (ACT-008). Se pide
   una vez más antes de darse por vencido, y si vuelve cortada el error explica
   que conviene subir `UBICATE_MAX_TOKENS`.

Y una prueba estaba mal, no el código: `test_eco_es_el_valor_por_defecto`
construía `Settings()` a secas, que **lee el `.env` de quien corre las
pruebas**. En una máquina con API key configurada fallaba sin que hubiera nada
roto. Ahora usa `_env_file=None`, que es lo que la prueba quería decir.

Resultado: **79 pruebas, todas pasando**, sin exclusiones.

> La forma exacta del `extra_body` que espera Gemini sale de lo que
> especifican las pruebas del repositorio. Conviene confirmarla contra el
> proveedor con `make probar` la primera vez que se use con una API key real.

## Las pantallas de carga

Dos fallas distintas, las dos encontradas mirando la aplicación:

**La portada no se veía como pantalla.** Se dibujaba pequeña, arriba del
formulario, en vez de taparlo. Causa: sus estilos vivían en `tema.CSS`, que la
pantalla de acceso **no inyecta** —esa pantalla trae su propio CSS—, así que la
portada salía sin estilo. Ahora el estilo viaja dentro de la propia pantalla.

**La bienvenida aparecía ya desvanecida.** Streamlit reutiliza el mismo nodo
del DOM para los dos `st.markdown`, y como las dos pantallas usaban el mismo
nombre de animación, el navegador la daba por consumida: la capa existía, con
`opacity: 0`. Ahora cada pantalla trae su propio nombre de animación.

De paso, la barra lateral y la cabecera se pintaban por encima de la capa;
ahora aparecen junto con el resto en vez de asomarse durante la espera.

## El plano de entrada

`panel_mapa.py` — en la versión de desarrollo el plano del piso -1 se muestra
apenas se entra, sin esperar a que se busque una sala. Si se busca algo de otro
piso, se cae al único plano levantado en vez de dejar la pantalla vacía.

## Cómo se probó

- `make ci` completo: `ruff` limpio, **79 pruebas**, validación de datos con 0
  errores y 0 avisos.
- Con el navegador, el flujo entero y midiendo la capa en cada paso:
  portada visible → se va → acceso → bienvenida visible → se va → aplicación
  con el plano del 851 ya cargado y sin el mapa del campus.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. El reintento ante respuesta cortada puede significar una llamada extra al modelo cuando la primera llega a medias |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No. `UBICATE_NIVEL_PENSAMIENTO` ya existía; recién ahora hace algo |
| ¿Requiere migración? | No |

## Al desplegar

Nada especial. Conviene correr `make probar` con la API key de producción para
confirmar que el modelo configurado acepta la opción de pensamiento; si no la
acepta, la aplicación sigue funcionando y lo deja en el log.

## Qué quedó pendiente

- **Pantalla de registro** (maqueta, láminas 4 y 5): depende de que haya
  cuentas de verdad (ADR-0010).
- **Menú y avatar en la cabecera** de la maqueta.
- Lo del mapa interior que sigue abierto: los otros 12 pisos, el ruteo, y la
  sala "SALA DE CLASES 09" sin código confirmado (`DEUDA_DATOS.md` D-06).
