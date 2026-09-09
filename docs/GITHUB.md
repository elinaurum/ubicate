# Trabajar en GitHub con varias personas

## 1. Subir el repositorio la primera vez

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "feat: reestructuración v1.0.0 con documentación"
git branch -M main
git remote add origin https://github.com/USUARIO/ubicate.git
git push -u origin main
```

Antes de `git add .`, confirmar que `.env` **no** aparece:

```bash
git status --short | grep -F ".env"    # solo debe salir .env.example
```

`.gitignore` ya lo excluye, junto con `var/` y `.streamlit/secrets.toml`. Una key
subida a GitHub queda en el historial aunque después se borre el archivo: si
pasa, hay que **rotar la key**, no basta con un commit de corrección.

## 2. Configuración del repositorio

**Público o privado.** Privado mientras se estabiliza. Los datos de contacto de
`data/kb/` son públicos, pero conviene revisarlos con la facultad antes de
abrirlo.

**Proteger `main`** (Settings → Branches → Add rule):

- Requerir pull request antes de fusionar.
- Requerir que pase el check de CI.
- Requerir al menos una aprobación.

Con esto nadie —incluido quien creó el repositorio— rompe `main` por accidente,
que es el accidente más común en equipos que recién empiezan a colaborar.

**Colaboradores:** Settings → Collaborators. Rol `Write` alcanza.

## 3. Flujo de trabajo diario

```bash
git checkout main && git pull            # partir siempre actualizado
git checkout -b feat/buscador-por-piso
# … trabajar …
make ci                                  # antes de subir, no después
git add -A && git commit -m "feat: permitir filtrar por piso"
git push -u origin feat/buscador-por-piso
```

En GitHub: abrir el pull request, completar la plantilla, pedir revisión.

Prefijos de rama y de commit: `feat/`, `fix/`, `datos/`, `docs/`, `refactor/`,
`test/`, `infra/`.

## 4. Repartir el trabajo sin pisarse

La estructura por capas permite trabajar en paralelo con pocos conflictos:

| Frente | Archivos | Requiere saber |
|---|---|---|
| Contenidos | `data/kb/*.md` | Markdown y la facultad. Cero Python |
| Datos del campus | `data/*.json` | JSON y el plano |
| Mapa | `src/ubicate/mapa/` | folium |
| Chat | `src/ubicate/chat/` | prompts, recuperación |
| Interfaz | `src/ubicate/ui/` | Streamlit |
| Infraestructura | `Dockerfile`, `.github/` | despliegue |

El frente de contenidos es el de mayor impacto por hora invertida, y no exige
programar. Quien conozca bien la facultad puede aportar desde ahí sin tocar
código.

Los conflictos de merge en JSON son molestos: coordinar quién edita
`edificios.json` y `salas.json` en un momento dado, o dividir por bloques.

## 5. Secretos en GitHub

Las API keys nunca van al repositorio ni a los issues. Si el CI llegara a
necesitar una, va en Settings → Secrets and variables → Actions. El CI actual no
la necesita: corre en modo eco.

## 6. Issues como cola de trabajo

Etiquetas sugeridas: `datos`, `bug`, `mapa`, `chat`, `ui`, `docs`,
`buena-primera-tarea`.

Las consultas sin respuesta del registro (ver [OPERACION.md](OPERACION.md) §3)
son la mejor fuente de issues: son necesidades reales de usuarios, no ideas.
