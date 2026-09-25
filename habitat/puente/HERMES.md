# Conectar el Hábitat con tus bots de Hermes

El hábitat corre en tu computadora, la misma donde está Hermes. Un pequeño programa, `servidor.py`, hace cuatro cosas:

1. Te muestra el hábitat en el navegador, en `http://127.0.0.1:8787`.
2. Lleva a tus bots lo que escribes en el chat y tus decisiones de aprobación. Lo hace por la API local de Hermes, así que responde el bot real, con ChatGPT como cerebro.
3. Publica sus respuestas en el hábitat y suma los tokens que consumen.
4. Si conectas tu calendario, avisa cuando se acerca un evento y le pide a Sylvia que prepare al equipo (ver *Sala de Eventos*).

Los bots, a su vez, avisan lo que hacen con `reportar.py`: tareas, avances, mensajes, pedidos de aprobación y eventos.

El hábitat no sale a internet: solo se puede abrir desde tu computadora. Lo único que busca afuera es tu calendario, si lo conectas.

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
6. (Opcional) Sala de Eventos: en RUTA/puente/bots.json deja lista la parte
   "calendario": {"ics": ["PEGA-AQUI-LA-DIRECCION-SECRETA"], "dias": 30,
   "cada_minutos": 10, "etiqueta": null} para que yo pegue la dirección a mano.
   No me pidas esa dirección por el chat.
7. Abre el hábitat con: python3 RUTA/puente/servidor.py
No me muestres las claves en el chat.
```

Dale la dirección del calendario solo en tu conversación privada con Sylvia. Nunca la pegues en **# Equipo** ni en un grupo. Si prefieres que nadie más la vea, pégala tú misma en `bots.json` (ver *Sala de Eventos*).

## Opción manual

1. En el `.env` de cada perfil de Hermes (`~/.hermes/.env` para el principal y `~/.hermes/profiles/<perfil>/.env` para los demás) agrega:
   ```
   API_SERVER_ENABLED=true
   API_SERVER_KEY=una-clave-larga-y-distinta-por-bot
   ```
2. Reinicia el gateway de Hermes.
3. Copia `puente/bots.ejemplo.json` como `puente/bots.json` y pega la clave de cada bot. Revisa que `perfil` sea el nombre del perfil en Hermes.
4. (Opcional) Conecta tu calendario en el bloque `calendario` (ver *Sala de Eventos*).
5. Abre el hábitat (ver abajo).

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
- Para agendar un evento en la Sala de Eventos:
    --evento-nuevo "Título" --fecha 2026-09-26T08:00 [--fin 2026-09-26T13:00]
    [--zona America/Bogota] [--lugar "Lugar"] [--descripcion "Texto"]
  · La hora es de Santo Domingo, o de --zona si la indicas. Con solo la fecha
    (2026-10-03), el evento es de todo el día.
  · El script muestra el id del evento, por ejemplo her-1790000000000.
- Si trabajas para un evento, agrega --evento ID a --tarea-para, --aprobacion y
  --presentar. El id viene en el aviso del evento o en la tarea que te asignaron.

Textos cortos y profesionales. Nunca incluyas datos sensibles de clientes
(cédulas, cuentas, montos, teléfonos), tampoco en los eventos. Nada se envía
ni se publica hacia clientes sin la aprobación de María Andrea.
```

## Sala de Eventos

La Sala de Eventos está a la derecha del Meeting Room. Muestra tus próximos eventos con su cuenta regresiva. Cuando se acerca uno, avisa en **# Equipo** y le pide a Sylvia que prepare al equipo.

Los eventos llegan de tres formas:
- De tu calendario de Google (lo más cómodo, ver abajo).
- Desde el botón *Eventos* del hábitat, con *Agregar evento*.
- Desde un bot, con `reportar.py --evento-nuevo`.

### Conectar tu calendario

Lo más ordenado es un calendario aparte, solo para los eventos de la empresa:

1. En Google Calendar, junto a *Otros calendarios*, toca **+** → *Crear calendario*. Llámalo **Eventos Madreperla**.
2. Anota ahí tus eventos: torneos, ferias, lanzamientos, visitas.
3. Abre la configuración de ese calendario: los tres puntos junto a su nombre → *Configuración y uso compartido*. Baja hasta *Integrar el calendario* y copia la **Dirección secreta en formato iCal** (termina en `.ics`).
4. Pégala en `puente/bots.json`, en el bloque `calendario`:
   ```json
   "calendario": { "ics": ["PEGA-AQUI-LA-DIRECCION-SECRETA"], "dias": 30, "cada_minutos": 10, "etiqueta": null }
   ```
5. Cierra el hábitat y vuelve a abrirlo. Al arrancar, la terminal dice *Sala de Eventos: 1 calendario(s), próximos 30 días.*

**¿Prefieres tu calendario de siempre?** Copia la dirección secreta de tu calendario principal y pon `"etiqueta": "#madreperla"`. Así la sala solo toma los eventos que tengan `#madreperla` en el **título** (da igual si va en mayúsculas). Se mira solo el título porque una invitación de otra persona puede traer cualquier cosa en la descripción. En la sala, la etiqueta no se ve en el título.

| Clave | Qué hace | Si no la pones |
|---|---|---|
| `ics` | Las direcciones secretas de tus calendarios, entre comillas y separadas por comas | No se lee ningún calendario |
| `dias` | Cuántos días hacia adelante se leen | 30 |
| `cada_minutos` | Cada cuántos minutos se revisa el calendario | 10 |
| `etiqueta` | Solo toma los eventos con ese texto (`null` = todos) | Todos |

**Esa dirección es secreta.** Con ella cualquiera puede ver tu calendario. Queda solo en `puente/bots.json`: la página no la muestra, no se guarda en `estado.json` y la terminal solo dice "calendario 1 (calendar.google.com)". Nunca la pegues en el chat del hábitat, en **# Equipo** ni en un grupo. Si crees que alguien la vio, en la misma pantalla de Google toca *Restablecer* junto a la dirección y pega la nueva en `bots.json`.

Ten en cuenta:
- Los cambios en Google pueden tardar un rato en llegar a la sala.
- Si cambias el título de un evento, se actualiza sin repetir los avisos. Si cambias la fecha o la hora, cuenta como un evento nuevo y los avisos empiezan otra vez.
- Los eventos que se repiten (por ejemplo, cada semana) solo aparecen en su primera fecha. Para un evento importante, créalo como evento único.
- Un evento sin hora de fin dura 2 horas. Uno de todo el día dura el día completo.
- Los eventos salen de la sala 3 días después de terminar.

### Qué avisos llegan y cuándo

| Aviso | Cuándo llega | Qué dice en # Equipo | ¿Sylvia prepara al equipo? |
|---|---|---|---|
| `7d` | Faltan 7 días o menos | "Falta una semana o menos para «…»" | Sí |
| `2d` | Faltan 48 horas o menos | "Faltan 2 días para «…»" | Sí, y puede presentarte un briefing |
| `1d` | Faltan 24 horas o menos | "Mañana es «…»" (o "Hoy es…", si es más tarde ese mismo día) | Sí |
| `3h` | Faltan 3 horas o menos | "En menos de 3 horas empieza «…»" | No, solo avisa |
| `ahora` | Mientras dura el evento | "Ya empezó «…»" | No, solo avisa |
| `despues` | Al terminar (hasta 3 días después) | "Terminó «…». Es buen momento para el seguimiento." | Sí, organiza el seguimiento |

Cada aviso llega una sola vez, con la fecha y la hora del lugar del evento. Por ejemplo: *Faltan 2 días para «Torneo de golf Bogotá» (sábado 26 de septiembre, 08:00 · Bogotá).* Si agregas un evento cuando falta un día, solo llega "Mañana es…", no los avisos anteriores.

### Qué hace Sylvia sola

En los avisos `7d`, `2d`, `1d` y `despues`, Sylvia recibe los datos del evento y:

1. **Reparte de 3 a 6 tareas** a los bots adecuados según su rol. Cada tarea queda vinculada al evento y se ve en su plan de preparación.
2. **Pide tu aprobación** para todo lo que vaya a clientes o al público: invitaciones, publicaciones, mensajes. Quedan como borradores en *Aprobaciones* hasta que decidas.
3. **A 2 días, puede presentarte un briefing** del evento en la pantalla del Meeting Room.
4. **Después del evento, organiza el seguimiento:** agradecimientos (como borradores para aprobar), contactos nuevos para el CRM y un resumen de resultados.
5. **Te deja un resumen** de 3 a 5 puntos en **# Equipo**.

Nunca envía ni publica nada sin tu aprobación, y no decide temas legales, contractuales ni precios.

También puedes tocar **Preparar ahora** en el panel *Eventos* cuando quieras. Y puedes ajustar dos cosas en `bots.json`:
- `"eventos_automaticos"`: en qué avisos prepara Sylvia al equipo. Por defecto `["7d", "2d", "1d", "despues"]`. Con `[]` solo llegan los avisos y tú decides cuándo preparar.
- `"max_preparaciones_hora"`: cuántos eventos prepara como máximo por hora, para no saturar al equipo. Por defecto 6.

### Eventos y tareas desde los bots

Un bot puede agendar un evento:

```
python3 RUTA/puente/reportar.py --bot @sylvia --evento-nuevo "Torneo de golf Bogotá" --fecha 2026-09-26T08:00 --zona America/Bogota --lugar "Club El Rincón"
```

- Opcionales: `--fin`, `--zona`, `--lugar` y `--descripcion`.
- El script responde con el id del evento (por ejemplo `her-1790000000000`). Si ese evento ya existía, lo dice y no lo repite.

Para que una tarea, una aprobación o una presentación aparezca en el plan del evento, se agrega `--evento ID`:

```
python3 RUTA/puente/reportar.py --bot @sylvia --tarea-para @contenido-madreperla --mensaje "Borrador de invitación al torneo" --evento her-1790000000000
```

Cuando Sylvia reparte las tareas de un evento, el hábitat le recuerda a cada bot que use `--evento` en sus aprobaciones y presentaciones.

## Leads y correos (Mark)

Mark lee la página de Madreperla y la hoja **Inventario de proyectos**, registra los leads y prepara correos con la identidad de Madreperla. **Ningún correo sale sin que lo apruebes.**

### 1. Conectar la hoja de inventario

1. Abre la hoja *Inventario de proyectos* en Google Sheets.
2. Toca **Compartir** › *Acceso general* › **Cualquier persona con el enlace** › *Lector*. Copia el enlace.
   (Otra opción: *Archivo › Compartir › Publicar en la web* › la pestaña del inventario › *Valores separados por comas (.csv)*.)
3. Pega el enlace en `puente/bots.json`, en `"inventario": "…"`. Cierra y vuelve a abrir el hábitat.

Quien tenga el enlace podrá ver la hoja. Si el inventario tiene datos internos (comisiones, notas privadas), deja esas columnas en otra pestaña y comparte solo la del inventario público.

En `"correo"` de `bots.json` puedes ajustar la firma, el teléfono y el remitente de los correos.

### 2. Instrucción para Mark

Copia esto en las instrucciones de Mark (cambia `RUTA` por la carpeta del hábitat):

```
Leads y correos de Madreperla:
- Para conocer la oferta, lee la página y el inventario (el inventario es la fuente más actualizada):
  python3 RUTA/puente/reportar.py --bot @mark --sitio
  python3 RUTA/puente/reportar.py --bot @mark --inventario
- Registra solo personas que mostraron interés en Madreperla: escribieron por el sitio, WhatsApp o redes,
  dejaron sus datos en un evento o llegaron referidas. No compres listas ni tomes correos de desconocidos
  de internet. No guardes cédulas, pasaportes, cuentas bancarias ni datos financieros.
  python3 RUTA/puente/reportar.py --bot @mark --lead "Nombre" --email correo@dominio.com --pais "País" --interes "Qué busca" --origen "Cómo llegó" --puntaje 1-5
- Para ver los leads: python3 RUTA/puente/reportar.py --bot @mark --leads
- Para cada lead calificado, redacta un correo en español formal (de "usted"), elegante y sereno, sin
  exclamaciones, sin urgencia y sin promesas de rentabilidad. Usa solo proyectos y datos del inventario
  o de la página. Precios, condiciones y plazos: "por confirmar con nuestro equipo".
  Guarda el texto en un archivo y envíalo a aprobación:
  python3 RUTA/puente/reportar.py --bot @mark --correo-para "Nombre <correo@dominio.com>" --asunto "Asunto" --archivo correo.txt
  Formato del texto: línea en blanco = párrafo nuevo · "## " = subtítulo · "- " = lista ·
  **negrita** · una línea "[Agendar una conversación](https://madreperlarealtors.com/en/contacto/)" = botón.
  No escribas la firma: el hábitat la agrega.
- Nunca envíes un correo tú. Espera la aprobación de María Andrea en el hábitat.
  Si lo devuelve, ajústalo según su comentario y vuelve a enviarlo a aprobación.
```

### 3. Qué ves en el hábitat

- En **Aprobaciones** aparece el correo con el destinatario, el asunto y la vista previa tal como lo verá el cliente. *Ver en tamaño real* lo abre en grande.
- Si lo **devuelves**, tu comentario le llega a Mark y te trae una versión nueva.
- Si lo **apruebas**, el correo queda como archivo en la carpeta `correos` del hábitat. Toca **Abrir en Mail para enviar**:
  - En **Outlook** se abre listo para enviar.
  - En **Apple Mail** se abre el mensaje; ve al menú *Mensaje › Volver a enviar*, revisa y envía.
- En la pestaña **Leads** ves cada lead con su país, su interés, su origen, su puntaje y su etapa.

Si más adelante prefieres que Mark envíe los correos aprobados por su cuenta, cambia `"envio": "borrador"` por `"envio": "bot"` en `bots.json`. Mark tiene que tener acceso al correo en Hermes, y solo puede enviar la versión exacta que aprobaste.

## Qué pasa con cada acción

| Tú haces en el hábitat | Qué pasa |
|---|---|
| Escribes en privado a un bot | Le llega a ese bot y su respuesta aparece en el chat |
| Escribes en **# Equipo** | Le llega a Sylvia, o al bot que menciones con @ |
| Apruebas o devuelves una solicitud | El bot recibe tu decisión y tu comentario, y te confirma qué hará |
| Apruebas un correo | Queda listo en la carpeta `correos` para que lo envíes desde tu cuenta, y Mark recibe la confirmación |
| Convocas una reunión | Todos van al Meeting Room por 10 minutos y Sylvia abre la reunión |
| Le pides a un bot que presente | Prepara su presentación y la muestra con `--presentar`: camina al atril y aparece en la pantalla grande |
| Anotas un evento en tu calendario de Madreperla | Aparece en la Sala de Eventos en unos 10 minutos |
| Agregas un evento con el botón *Eventos* | Aparece al momento. Si ya está cerca, llega el aviso enseguida |
| Tocas *Preparar ahora* en un evento | Sylvia reparte tareas para ese evento y te deja un resumen en **# Equipo** |
| Se acerca un evento | Llega un aviso a **# Equipo** y, según cuánto falte, Sylvia prepara al equipo (ver *Qué avisos llegan y cuándo*) |
| Borras un evento | Los que agregaste en el hábitat se borran ahí. Los del calendario, bórralos en el calendario |

Además:
- Cuando un bot le asigna una tarea a otro con `--tarea-para`, se la hace llegar. Para evitar bucles, el límite es de 6 reenvíos cada 10 minutos.
- Las tareas, aprobaciones y presentaciones con `--evento` aparecen en el plan de preparación de ese evento.
- La ficha de cada bot suma sola los tokens de cada respuesta.

## Seguridad

- El hábitat solo se abre desde tu computadora (`127.0.0.1`). Otras páginas web no pueden enviarle mensajes a tus bots.
- Las claves y la dirección secreta de tu calendario quedan en `puente/bots.json`. Ese archivo no se sube a GitHub y la página no lo muestra.
- Los leads y los correos completos (destinatario, texto) quedan en `puente/privado.json` y los correos aprobados en la carpeta `correos`. Ninguno de los dos se sube a GitHub ni se ve fuera de tu computadora. En `estado.json` solo queda el asunto del correo.
- `estado.json` tiene las conversaciones del día y los eventos. No se sube a GitHub, salvo que un bot use `reportar.py --subir` (solo hace falta si publicas el hábitat con GitHub Pages). En ese caso también se suben el título, el lugar y la descripción de los eventos, así que no anotes datos sensibles de clientes en ellos.
- Cualquiera puede enviarte una invitación y hacer que aparezca en tu calendario principal. Por eso lo más seguro es el **calendario aparte**, donde solo tú agregas eventos. La etiqueta ayuda, pero alguien podría enviarte una invitación con `#madreperla` en el título. En todos los casos, a Sylvia le llegan solo el título, la fecha y el lugar (nunca la descripción del calendario), marcados como información y no como órdenes, y nada sale hacia clientes sin tu aprobación.

## Si algo no funciona

| Si ves | Qué revisar |
|---|---|
| "No pude comunicarme con…" | Que Hermes y su gateway estén abiertos |
| "La clave de … no es correcta" | La clave de ese bot en `puente/bots.json` |
| "… todavía no está conectado" | Que ese bot esté en `puente/bots.json` |
| Arriba dice *Simulación* | Que abriste `http://127.0.0.1:8787` y no el archivo directamente |
| Al abrir, la terminal no dice *Sala de Eventos: 1 calendario(s)…* | Que la dirección esté dentro de `"ics": ["…"]`, con comillas y corchetes. Después de cambiar `bots.json`, cierra y vuelve a abrir el hábitat |
| En la terminal: "No pude leer el calendario 1…: el servidor respondió 404" (o 401 o 403) | La dirección secreta cambió, por ejemplo si la restableciste. Cópiala de nuevo desde Google Calendar y pégala en `puente/bots.json` |
| En la terminal: "…no hubo conexión con el servidor del calendario" o "…tardó demasiado en responder" | La conexión a internet. Los eventos que ya estaban se conservan y se vuelve a intentar solo |
| Un evento del calendario no aparece en la sala | Que sea dentro de los próximos 30 días. Si usas `etiqueta`, que el título diga `#madreperla`. Si se repite, solo aparece su primera fecha. Google puede tardar un rato en actualizarlo |
| "Todavía no hay bots conectados…" al tocar *Preparar ahora* | Que exista `puente/bots.json` y que Sylvia esté en él |
| "Ya se lo pedí a Sylvia hace un momento" | Sylvia ya está preparando ese evento. Espera un minuto antes de pedírselo de nuevo |
| "No le pedí a Sylvia que preparara «…» para no saturar al equipo" | Ya preparó 6 eventos en la última hora. Pídeselo más tarde con *Preparar ahora* |
| "Este evento viene de tu calendario…" | Bórralo en Google Calendar. Sale de la sala en unos minutos |
| "No conozco la zona horaria…" | Usa un nombre como `America/Bogota`, `America/Santo_Domingo` o `America/New_York` |
| "No pude leerlo: falta \"inventario\"…" | Pega el enlace de la hoja en `"inventario"` de `puente/bots.json` |
| "Google devolvió una página, no la hoja" | La hoja no está compartida con *Cualquier persona con el enlace*. Revisa el paso 1 de *Leads y correos* |
| El correo aprobado no se abre con *Abrir en Mail* | Ábrelo a mano: está en la carpeta `correos` del hábitat (doble clic) |
| Una tarea de un evento quedó en el chat, pero el bot no respondió | Se llegó al límite de 6 reenvíos en 10 minutos (la terminal dice "Límite de reenvíos alcanzado"). Pasa si se preparan varios eventos a la vez. Vuelve a pedírsela en unos minutos |
