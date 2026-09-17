# ACT-012 — Agregar la pantalla de acceso y separar las dos versiones

| Campo | Valor |
|---|---|
| Fecha | 2026-09-17 |
| Versión | 2.1.0 |
| Tipo | funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

Pausar el trabajo del mapa y hacer una pantalla de inicio de sesión **sin
integrar cuentas todavía**, solo para que no cualquiera pueda usar la
aplicación web, y con dos vistas según la contraseña: `user` muestra la última
versión funcional (el mapa del campus) y `developer` muestra además el plano
interior, que es lo que está en obra. El equipo entregó la maqueta con los
colores.

## Qué se hizo

- `src/ubicate/acceso.py` — nuevo. `Rol` (`usuario`, `desarrollo`) y
  `rol_para(clave, settings)`. Vive fuera de `ui/` para probarse sin Streamlit
  (ADR-0001). La comparación usa `secrets.compare_digest`.
- `src/ubicate/config.py` — `acceso_activo`, `clave_usuario`,
  `clave_desarrollo`, reemplazables por `UBICATE_CLAVE_USUARIO` y
  `UBICATE_CLAVE_DESARROLLO`.
- `src/ubicate/ui/componentes/pantalla_acceso.py` — nuevo. La pantalla, con
  los colores de la maqueta (fondo `#2C3E5C`, botón `#E63329`, secundario
  `#7391B5`) y la chincheta con la U como SVG en línea.
- `src/ubicate/ui/app.py` — la puerta va **antes** de cargar los datos: quien
  no entró no ve la aplicación ni sus posibles errores.
- `src/ubicate/ui/estado.py` — `rol()`, `fijar_rol()`, `modo_desarrollo()`,
  `salir()`.
- `src/ubicate/ui/componentes/panel_mapa.py` — el plano interior del piso solo
  aparece en modo desarrollo.
- `src/ubicate/ui/componentes/barra_lateral.py` — muestra qué versión se está
  viendo y un botón "Salir".

## Por qué así

Ver [ADR-0010](../decisiones/ADR-0010-puerta-de-acceso-sin-cuentas.md).

**Esto no es autenticación y quedó dicho en tres lugares** (el módulo, el ADR y
la propia pantalla): la clave por defecto está en el repositorio, una clave
compartida no se revoca por persona, y no hay límite de intentos. Cumple lo que
se pidió —que la herramienta a medio construir no quede abierta— y nada más.

Dos decisiones de detalle:

- **El mensaje de error es uno solo** ("Esa contraseña no es correcta"), igual
  para clave vacía, equivocada o de otro rol: decir cuál falló le regalaría
  información a quien esté probando.
- **No se registra ningún intento de acceso.** `docs/PRIVACIDAD.md` promete que
  no se guarda ningún identificador de la persona, y un registro de intentos
  con correos sería justamente eso.

## Cómo se probó

- `tests/test_acceso.py` — nuevo: cada clave abre su rol, una clave
  equivocada o vacía no abre nada, distingue mayúsculas, perdona espacios
  alrededor, una clave sin configurar deja la puerta cerrada (no abierta), y
  si las dos claves fueran iguales gana la de desarrollo.
- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 63 ok.
- `ruff check src tests scripts`: limpio.
- **Verificación en la aplicación de verdad**, con el navegador: se levantó la
  app, se sacó captura de la pantalla y se recorrió el flujo con cada clave.
  - `user` → entra, barra lateral "Versión estable", busca B04, ve la ficha,
    **no** se le ofrece el interior del piso.
  - `developer` → entra, "Versión en desarrollo", busca B04, ve la ficha **y**
    "Ver el interior del piso -1".
  - `cualquiera` → no entra.
  - La primera captura mostró el botón azul y los campos cuadrados: los
    selectores CSS apuntaban a `data-baseweb`, que esta versión de Streamlit ya
    no usa. Se corrigieron a `data-testid` y se volvió a comprobar.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | Sí, a propósito: la aplicación ya no se abre sin clave. Con `UBICATE_ACCESO_ACTIVO=false` vuelve al comportamiento anterior |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No obligatorias, pero **en cualquier despliegue expuesto hay que fijar** `UBICATE_CLAVE_USUARIO` y `UBICATE_CLAVE_DESARROLLO` |
| ¿Requiere migración? | No |

## Al desplegar

1. Fijar las dos claves como secreto, **no dejar las del repositorio**:

   ```toml
   UBICATE_CLAVE_USUARIO = "…"
   UBICATE_CLAVE_DESARROLLO = "…"
   ```

2. Entregar la clave de usuario por el canal que corresponda. Si se filtra, se
   cambia el secreto y se vuelve a desplegar: no hay forma de revocarla a una
   sola persona.

## Qué quedó pendiente

- **Cuentas de verdad** (ROADMAP §6). Esta pantalla es el paso previo: cuando
  lleguen, solo cambia de dónde sale el rol.
- **"Olvidé la contraseña" y "REGISTRARSE" no funcionan**: están porque la
  maqueta los tiene, y explican que todavía no hay cuentas.
- **El campo de correo se pide y no se usa.** Se avisa en la pantalla.
- **Sin límite de intentos.** Con una clave compartida y sin datos personales
  detrás, no se consideró necesario; si la aplicación se abre al público con
  clave, hay que agregarlo.
- **`tests/test_proveedores.py` sigue roto en `main`**, de antes de esta
  entrega; bloquea `make ci` completo.
