# ADR-0001 · Arquitectura por capas con el dominio separado de Streamlit

- **Estado:** aceptada
- **Fecha:** 2026-09-08
- **Reemplaza a:** —

## Contexto

El prototipo era un único `app.py` de 340 líneas donde la carga de datos, la
búsqueda, la construcción del mapa y la interfaz estaban entrelazadas. Cada
comportamiento solo se podía verificar levantando la aplicación y probando a
mano, así que en la práctica no se verificaba. Con un equipo que rota cada
semestre, eso vuelve el código intocable: nadie se atreve a cambiar algo que no
sabe cómo probar.

## Decisión

Separar en capas con dependencias en una sola dirección:

```
ui → chat / mapa → datos / busqueda → modelos / config
```

**Ningún módulo fuera de `ui/` importa Streamlit.**

## Consecuencias

**A favor**

- El motor, la búsqueda y el mapa se prueban sin levantar la aplicación; de ahí
  salen las 30 pruebas que corren en segundos.
- Migrar a otra interfaz (FastAPI + React, una app móvil) no toca el dominio.
- Los límites entre capas dicen dónde va cada cosa nueva, que es el problema
  real cuando entra alguien al equipo.

**En contra**

- Más archivos que un script único. Para un prototipo de dos semanas sería
  sobreingeniería; para algo que va a operar con la facultad, es lo mínimo.
- Hay que resistir el atajo de importar `streamlit` en el dominio para mostrar un
  aviso rápido. El linter y las pruebas lo detectan.
