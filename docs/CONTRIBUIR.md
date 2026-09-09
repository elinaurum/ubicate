# Cómo contribuir

## Regla central: cada cambio se documenta

Ningún cambio entra a `main` sin su rastro escrito. El costo es de diez minutos
y evita el problema que hace inmantenibles a los proyectos universitarios: que el
conocimiento se vaya con la persona que se tituló.

Para cada cambio entregado:

1. **Nota de actualización.** Copiar `docs/actualizaciones/PLANTILLA.md` a
   `docs/actualizaciones/ACT-NNN-descripcion-corta.md` y completarla. El número
   es correlativo y no se reutiliza.
2. **Entrada en el CHANGELOG.** Bajo la versión correspondiente, en la categoría
   que corresponda (Agregado / Cambiado / Corregido / Seguridad), enlazando la
   nota.
3. **ADR, si la decisión es estructural.** Si el cambio condiciona decisiones
   futuras (elegir una tecnología, cambiar el modelo de datos, cambiar la forma
   de desplegar), agregar `docs/decisiones/ADR-NNNN-titulo.md`. Un ADR no se
   edita una vez aceptado: se supera con otro que lo reemplace.
4. **Actualizar la documentación afectada.** Si tocaste el esquema de datos,
   `docs/DATOS.md`. Si tocaste el despliegue, `docs/DESPLIEGUE.md`.

## Flujo de trabajo

```bash
git checkout -b tipo/descripcion-corta     # feat/, fix/, datos/, docs/, infra/
# … cambios …
make ci                                    # lint + pruebas + validación de datos
git commit -m "tipo: descripción en imperativo"
```

Mensajes de commit: `tipo: descripción`, donde tipo es `feat`, `fix`, `datos`,
`docs`, `refactor`, `test` o `infra`.

## Antes de abrir un pull request

- [ ] `make ci` pasa en verde
- [ ] Hay nota en `docs/actualizaciones/`
- [ ] El CHANGELOG tiene la entrada
- [ ] Si cambió `data/`, `make validar` pasa sin avisos nuevos
- [ ] Si cambió el prompt, se subió `VERSION_PROMPT` en `chat/prompts.py`

## Convenciones de código

- El código y los comentarios están en español; es un proyecto de una facultad
  chilena y quien lo herede va a leer en español.
- Anotaciones de tipo en todo lo público.
- Las capas dependen en una sola dirección: `ui → chat/mapa → datos/busqueda →
  modelos/config`. Nada en `datos/`, `busqueda/`, `mapa/` o `chat/` importa
  Streamlit; por eso todo eso se puede probar sin levantar la aplicación.
- Ninguna cadena de configuración escrita a mano en el código: va en `config.py`.
