# Despliegue

## 1. Dimensionamiento para ~2.000 usuarios

2.000 personas en la facultad **no** son 2.000 sesiones simultáneas. El patrón
de uso de una app de orientación es de ráfagas: minutos antes del cambio de
bloque, primeras semanas del semestre, día de bienvenida a mechones.

Estimación de trabajo:

| Supuesto | Valor |
|---|---|
| Comunidad alcanzable | ~2.000 personas |
| Usan la app en un día activo | 15–25 % → 300–500 sesiones |
| Concurrencia en un pico | 3–6 % de las sesiones del día → 20–40 simultáneas |
| Consultas por sesión | 2–4 |

Un contenedor con 2 vCPU y 2 GB atiende cómodamente ese pico, porque el trabajo
pesado (datos, base de conocimiento, mapa) está cacheado por proceso y no por
usuario. El punto de partida recomendado es **2 réplicas** detrás de un
balanceador: no por capacidad, sino para poder desplegar sin caída y sobrevivir
al reinicio de una.

**Antes de anunciarlo a la facultad, medir.** El cuadro de arriba son supuestos,
no observaciones. La primera semana da los números reales, y para eso está el
registro de consultas.

### Dónde está el límite real

No es la CPU: es el proveedor del modelo. Cada consulta al chat es una llamada
externa con latencia de segundos y costo por token. Por eso existen:

* `UBICATE_MENSAJES_POR_SESION` — tope por sesión (60 por defecto);
* `UBICATE_SEGUNDOS_ENTRE_MENSAJES` — frecuencia mínima entre mensajes;
* **modo eco** — si el proveedor cae o se agota el presupuesto, la aplicación
  sigue funcionando y responde con la base. Es degradación, no caída.

Cambiar a modo eco no requiere desplegar: basta `UBICATE_PROVEEDOR_LLM=eco` y
reiniciar.

## 2. Fijar versiones antes de producción

`requirements.txt` usa rangos, cómodo para desarrollar y riesgoso para desplegar.
Antes de la primera puesta en producción:

```bash
pip freeze > requirements.lock
```

y usar `requirements.lock` en el `Dockerfile`. Que un despliegue traiga una
versión nueva de Streamlit sin que nadie lo haya decidido es una fuente de caídas
difíciles de diagnosticar.

## 3. Docker

```bash
docker build -t ubicate:1.0.0 .
docker run -d --name ubicate -p 8501:8501 --env-file .env \
  -v ubicate_var:/app/var ubicate:1.0.0
```

El volumen en `/app/var` conserva el registro de consultas entre reinicios.

El contenedor corre como usuario sin privilegios y trae healthcheck contra
`/_stcore/health`, que es también la ruta que debe usar el balanceador.

## 4. Proxy inverso

Streamlit necesita **WebSockets**. Si el proxy no los reenvía, la aplicación
carga y queda congelada — es el error de despliegue más frecuente.

```nginx
server {
    listen 443 ssl;
    server_name ubicate.ing.uchile.cl;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

Con varias réplicas, el balanceador debe usar **sesiones pegajosas**: el estado
de la conversación vive en memoria del proceso, así que un usuario que salte de
réplica pierde su historial.

## 5. Secretos

La API key nunca va al repositorio. Opciones, en orden de preferencia:

1. Gestor de secretos de la infraestructura de la facultad.
2. Variables de entorno inyectadas por el orquestador.
3. `.streamlit/secrets.toml`, que ya está en `.gitignore`.

Si una clave se filtra: rotarla primero, investigar después.

## 6. Lista de verificación

- [ ] `make ci` en verde sobre el commit que se despliega
- [ ] Versiones fijadas (`requirements.lock`)
- [ ] `.env` de producción con `UBICATE_ENTORNO=produccion` y `UBICATE_LOG_FORMATO=json`
- [ ] API key inyectada como secreto, no en la imagen
- [ ] HTTPS y WebSockets verificados
- [ ] Healthcheck respondiendo
- [ ] Volumen persistente para `/app/var`
- [ ] Etiqueta de versión de la imagen igual a la del CHANGELOG
- [ ] Prueba de humo: buscar `B04`, preguntar "dónde almuerzo", verificar el marcador

## 7. Volver atrás

Cada versión es una imagen etiquetada. La vuelta atrás es desplegar la etiqueta
anterior. Si el cambio tocó el esquema de `data/`, revisar en la nota de
actualización si requiere migración inversa antes de volver.
