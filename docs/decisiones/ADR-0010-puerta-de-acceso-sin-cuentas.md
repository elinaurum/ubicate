# ADR-0010 · Puerta de acceso con clave compartida, sin cuentas

- **Estado:** aceptada
- **Fecha:** 2026-09-17
- **Relacionado:** `docs/ROADMAP.md` §6 (perfil y persistencia entre sesiones),
  `docs/PRIVACIDAD.md`, ADR-0009 (la vista que queda detrás de la puerta)

## Contexto

La aplicación está en construcción y su URL es pública (Streamlit Community
Cloud, ver `docs/DESPLIEGUE.md` §8). El equipo pidió dos cosas a la vez:

1. que no entre cualquiera que tropiece con la dirección mientras se trabaja;
2. poder mostrar **la versión estable** a quien corresponda y **la que está en
   obra** —el mapa interior del piso, ADR-0009— solo a quien la está
   construyendo.

Cuentas de verdad (registro, correo, recuperación de clave) son otra cosa:
exigen resolver autenticación y política de datos personales, y el ROADMAP §6
ya dice que no es un cambio menor.

## Decisión

Una **clave compartida** que decide qué vista se muestra. No hay cuentas, no
hay usuarios y no se identifica a nadie.

1. `ubicate/acceso.py` —fuera de `ui/`, probable sin Streamlit— define `Rol`
   (`usuario`, `desarrollo`) y `rol_para(clave, settings)`.
2. Las claves viven en `config.py` (`clave_usuario`, `clave_desarrollo`) y se
   reemplazan por entorno con `UBICATE_CLAVE_USUARIO` y
   `UBICATE_CLAVE_DESARROLLO`.
3. `ui/componentes/pantalla_acceso.py` dibuja la pantalla según la maqueta del
   equipo. Va **antes** de cargar los datos: quien no entró no ve la
   aplicación ni sus errores.
4. El rol vive en el estado de sesión. `usuario` ve la aplicación estable;
   `desarrollo` ve además el plano interior del piso.
5. `UBICATE_ACCESO_ACTIVO=false` apaga la puerta entera (desarrollo local y
   pruebas).

### Esto no es seguridad

Queda dicho aquí para que nadie lo confunda más adelante:

- La clave por defecto **está en el repositorio**. Quien lee el código la sabe.
- Una clave compartida no se puede revocar por persona: si se filtra, se
  cambia para todos.
- No hay cifrado de sesión propio, ni límite de intentos, ni registro de quién
  entró. La aplicación no guarda datos personales, así que no hay nada que
  robar detrás de la puerta — es un portón, no una caja fuerte.

Sirve para lo que se pidió: que la herramienta a medio construir no quede
abierta al público, y separar dos vistas. Nada más.

## Alternativas consideradas

1. **Cuentas de verdad ahora.** Es el ROADMAP §6. Exige autenticación,
   almacenamiento de credenciales y una política de datos personales que hoy
   el proyecto no tiene (y que `docs/PRIVACIDAD.md` promete evitar: no se
   guarda ningún identificador de la persona). Desproporcionado para lo que se
   necesita, que es una puerta mientras se construye.
2. **Autenticación de la propia plataforma** (la de Streamlit Community Cloud,
   restringiendo por correo). Es más segura, pero ata el acceso a un proveedor,
   obliga a administrar una lista de correos —dato personal que hoy no se
   guarda— y no permite las dos vistas distintas, que era la mitad del pedido.
3. **Una sola clave y un interruptor aparte para la vista en obra.** Menos
   claro: quien entra tendría que saber además dónde está el interruptor. Dos
   claves cuentan la historia solas.

## Consecuencias

**A favor**

- La aplicación deja de estar abierta a cualquiera con la URL.
- El equipo puede mostrar la versión estable sin exponer lo que está a medio
  hacer, y trabajar en lo nuevo con la misma aplicación desplegada.
- `rol_para` se prueba sin levantar Streamlit (`tests/test_acceso.py`), igual
  que el resto del dominio.
- Cuando lleguen las cuentas, el punto de enganche está: `estado.rol()` ya
  decide qué se muestra, y solo cambia de dónde sale ese rol.

**En contra**

- La clave por defecto está en el repositorio: **hay que cambiarla por entorno
  en cualquier despliegue expuesto**, y eso es un paso que alguien tiene que
  acordarse de dar. `docs/DESPLIEGUE.md` §5 lo incluye en la lista de
  verificación.
- La pantalla muestra "Olvidé la contraseña" y "REGISTRARSE" porque están en
  la maqueta, pero no hacen nada todavía: explican que no hay cuentas. Es
  deuda de interfaz asumida a sabiendas.
- El campo de correo se pide y no se usa. Se avisa en la misma pantalla para
  no dar a entender que se está guardando algo.
