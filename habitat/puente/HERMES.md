# Conectar el Hábitat con tus bots de Hermes

El hábitat corre en tu computadora, la misma donde está Hermes. Un pequeño programa, `servidor.py`, hace tres cosas:

1. Te muestra el hábitat en el navegador, en `http://127.0.0.1:8787`.
2. Lleva a tus bots lo que escribes en el chat y tus decisiones de aprobación. Lo hace por la API local de Hermes, así que responde el bot real, con ChatGPT como cerebro.
3. Publica sus respuestas en el hábitat y suma los tokens que consumen.

Los bots, a su vez, avisan lo que hacen con `reportar.py`: tareas, avances, mensajes y pedidos de aprobación.

Nada de esto sale a internet. Solo se puede abrir desde tu computadora.

## Opción fácil: pídeselo a Sylvia

Hermes puede usar la terminal, así que puede dejar todo configurado por ti. Cambia `RUTA` por la carpeta donde guardaste el hábitat y pégale esto a Sylvia en Hermes:

```
Necesito conectar el Hábitat de Madreperla con Hermes. La carpeta está en RUTA.

1. Muéstrame la lista de perfiles con: hermes profile list
2. Para cada bot (sylvia, viktor, ageente-de-investigacion-madreperla,
   contenido-madreperla, mark, marcelo) activa el API server en su perfil:
   en su archivo .env agrega API_SERVER_ENABLED=true y una API_SERVER_KEY
   nueva, aleatoria y distinta para cada bot. No cambies nada más.
3. Reinicia el gateway para que tome los cambios.
4. Crea RUTA/puente/bots.json copiando RUTA/puente/bots.ejemplo.json y pon la
   clave y el nombre de perfil de cada bot. Si un bot es el perfil principal,
   usa "perfil": "default". Si algún perfil usa su propio puerto, agrega su
   dirección completa en "url" (por ejemplo "http://127.0.0.1:8643").
5. Prueba cada bot con una consulta a /v1/models y dime cuáles respondieron.
6. Abre el hábitat con: python3 RUTA/puente/servidor.py
No me muestres las claves en el chat.
```

## Opción manual

1. En el `.env` de cada perfil de Hermes (`~/.hermes/.env` para el principal y `~/.hermes/profiles/<perfil>/.env` para los demás) agrega:
   ```
   API_SERVER_ENABLED=true
   API_SERVER_KEY=una-clave-larga-y-distinta-por-bot
   ```
2. Reinicia el gateway de Hermes.
3. Copia `puente/bots.ejemplo.json` como `puente/bots.json` y pega la clave de cada bot. Revisa que `perfil` sea el nombre del perfil en Hermes.
4. Abre el hábitat (ver abajo).

## Abrir el hábitat cada día

- **Mac:** doble clic en `iniciar.command`. La primera vez, macOS puede pedir confirmación: clic derecho → *Abrir*.
- **Windows:** doble clic en `iniciar.bat`.
- **Terminal:** `python3 puente/servidor.py`

Se abre el navegador en `http://127.0.0.1:8787` y arriba a la izquierda dice **Conectado a Hermes**. Para cerrarlo, cierra la ventana de la terminal (o presiona Ctrl+C).

## Instrucción para cada bot

Pega esto en las instrucciones de cada bot. Cambia `@usuario-del-bot` por el suyo y `RUTA` por la carpeta del hábitat:

```
Reporta tu trabajo al Hábitat de Madreperla con la terminal:

  python3 RUTA/puente/reportar.py --bot @usuario-del-bot [opciones]

- Al empezar una tarea:    --estado trabajando --tarea "texto corto"
- Si avanzas:              --avance 50
- Al terminarla:           --terminada
- Si estás libre:          --estado inactivo
- Para hablar al equipo:   --mensaje "texto" --para todos
- Para hablar a otro bot:  --mensaje "texto" --para @otro-bot
- Para asignar una tarea:  --mensaje "tarea" --tarea-para @otro-bot
- Para pedir aprobación a María Andrea (antes de enviar o publicar algo):
    --aprobacion "Título corto" --detalle "Texto completo" --clase borrador|propuesta|consulta
- Para presentar tu trabajo en la pantalla del Meeting Room:
    --presentar "Título" --formato slides|documento|dashboard --archivo RUTA_DEL_ARCHIVO
  · slides: texto con diapositivas separadas por una línea ---; la línea con # es
    el título y las líneas con - son los puntos.
  · documento: texto con secciones que empiezan con # o ##.
  · dashboard: archivo JSON así:
    {"kpis":[{"nombre":"Leads nuevos","valor":"38","cambio":"+12%"}],
     "series":[{"nombre":"Leads por día","tipo":"barras","puntos":[["Lun",4],["Mar",7]]}]}
    ("tipo" puede ser "barras" o "linea").
  · Para apagar la pantalla al terminar: --terminar-presentacion

Textos cortos y profesionales. Nunca incluyas datos sensibles de clientes
(cédulas, cuentas, montos, teléfonos). Nada se envía ni se publica hacia
clientes sin la aprobación de María Andrea.
```

## Qué pasa con cada acción

| Tú haces en el hábitat | Qué pasa |
|---|---|
| Escribes en privado a un bot | Le llega a ese bot y su respuesta aparece en el chat |
| Escribes en **# Equipo** | Le llega a Sylvia, o al bot que menciones con @ |
| Apruebas o devuelves una solicitud | El bot recibe tu decisión y tu comentario, y te confirma qué hará |
| Convocas una reunión | Todos van al Meeting Room por 10 minutos y Sylvia abre la reunión |
| Le pides a un bot que presente | Prepara su presentación y la muestra con `--presentar`: camina al atril y aparece en la pantalla grande |

Además:
- Cuando un bot le asigna una tarea a otro con `--tarea-para`, se la hace llegar. Para evitar bucles, el límite es de 6 reenvíos cada 10 minutos.
- La ficha de cada bot suma sola los tokens de cada respuesta.

## Seguridad

- El hábitat solo se abre desde tu computadora (`127.0.0.1`). Otras páginas web no pueden enviarle mensajes a tus bots.
- Las claves quedan en `puente/bots.json`. Ese archivo no se sube a GitHub y la página no lo muestra.
- `estado.json` tiene las conversaciones del día y tampoco se sube a GitHub.

## Si algo no funciona

| El chat dice | Qué revisar |
|---|---|
| "No pude comunicarme con…" | Que Hermes y su gateway estén abiertos |
| "La clave de … no es correcta" | La clave de ese bot en `puente/bots.json` |
| "… todavía no está conectado" | Que ese bot esté en `puente/bots.json` |
| Arriba dice *Simulación* | Que abriste `http://127.0.0.1:8787` y no el archivo directamente |
