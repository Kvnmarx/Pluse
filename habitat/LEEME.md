# Hábitat de agentes · Madreperla

Laboratorio 3D donde viven los seis agentes de IA. Cada robot tiene su color y su sala.

| Bot (Hermes) | Usuario en Hermes | Color | Sala | Función |
|---|---|---|---|---|
| Sylvia  | `@sylvia` | Coral | Meeting Room (centro) | Coordina a los demás agentes |
| Viktor  | `@viktor` | Cian | Sala de Ventas | Asesor inmobiliario, ventas |
| Sergio  | `@ageente-de-investigacion-madreperla` | Verde | Librería | Investigación y verificación de fuentes |
| Bety    | `@contenido-madreperla` | Magenta | Design Room | Calendario y contenido (solo borradores) |
| Mark    | `@mark` | Ámbar | Analítica | Marketing y captación de leads |
| Marcelo | `@marcelo` | Violeta | Archivo | CRM y seguimiento de clientes |

El **Code Lab** queda libre para un futuro agente. El **Meeting Room** está en el centro del laboratorio.

**Tu avatar (María Andrea):** toca el piso para caminar. Cerca de un bot aparece *Hablar con…*, y dentro del Meeting Room, *Convocar reunión*. *Seguirme* hace que la cámara te acompañe.

**Conectar Hermes:** ver `puente/HERMES.md`. Para abrir el hábitat conectado a tus bots: doble clic en `iniciar.command` (Mac) o `iniciar.bat` (Windows).

**Aprobaciones:** el botón *Aprobaciones* (y la pantalla del Meeting Room) muestra lo que los bots te dejan para revisar. *Aprobar* pide un segundo toque para confirmar. *Devolver* pide un comentario con lo que hay que ajustar. Los bots con algo pendiente muestran un punto champagne junto a su nombre.

**Presentaciones:** en las reuniones, los bots pueden mostrar su trabajo como **diapositivas**, **documento** o **dashboard** (indicadores y gráficos). El presentador camina al atril, los demás miran la pantalla grande del Meeting Room y arriba aparece *"… presenta"* con el botón *Ver en grande*. También quedan en el chat y en la ficha de cada bot. Para pedir una, usa *Pedir presentación* en el chat privado o escribe "preséntame…". Los bots de Hermes presentan con `reportar.py --presentar` (ver `puente/HERMES.md`).

**Sala de Eventos:** queda a la derecha del Meeting Room, con un tablero de cuenta regresiva y un calendario en la pared. El botón *Eventos* (arriba) muestra cuántos eventos hay en los próximos 7 días y abre el panel con cada uno: fecha, lugar, cuánto falta y su plan de preparación, con las tareas del equipo y cómo van. Ahí puedes *Agregar evento* o tocar *Preparar ahora* para que Sylvia reparta las tareas. Cuando se acerca un evento llega un aviso a **# Equipo**: una semana antes, 2 días antes, el día antes, 3 horas antes, al empezar y al terminar. Con Hermes, la sala lee tu calendario de Google (ver `puente/HERMES.md`). En claude.ai lo lee con el conector de Google Calendar de tu cuenta: solo el calendario que elijas o los eventos con `#madreperla` en el título.

**Día y noche:** la luz sigue la hora real de Santo Domingo. En el selector junto al reloj puedes ver el laboratorio de mañana, al mediodía, al atardecer o de noche.

## Cómo funciona

- **Simulación:** sin `estado.json`, los robots trabajan, se reúnen, conversan y piden aprobaciones de ejemplo. Así se ve en claude.ai.
- **Conectado a Hermes:** abierto con `puente/servidor.py` en tu computadora. Lee `estado.json` cada 3 segundos, y el chat y las aprobaciones llegan a tus bots reales.
- **En vivo (solo lectura):** si la página se publica con `estado.json` en otro lugar, como GitHub Pages, muestra a los bots cada 15 segundos, pero no permite escribirles.

## Cómo conectar un agente real

Cada agente solo tiene que actualizar su línea en `estado.json` (copia `estado.ejemplo.json` como punto de partida):

```json
{ "id": "@contenido-madreperla", "estado": "trabajando", "tarea": "Redactando el calendario de octubre" }
```

- `id`: el usuario de Hermes del bot (`@sylvia`, `@contenido-madreperla`…) o su nombre corto (`sylvia`, `sergio`, `bety`, `mark`, `marcelo`, `viktor`).
- `estado`: `trabajando`, `pensando`, `reunion`, `inactivo` o `error` (este último hace parpadear al robot en rojo: necesita ayuda).
- `sala` (opcional): `code`, `design`, `analitica`, `libreria`, `archivo`, `ventas`, `meeting` o `eventos`. Si no se pone, el robot va a su propia sala (o al Meeting Room si está en reunión).
- `tarea`: texto corto que aparece en la burbuja del robot.

### Datos para la ficha del agente (todos opcionales)

Al tocar un robot o su nombre se abre su ficha a la derecha. Se llena con estos campos:

| Campo | Qué muestra |
|---|---|
| `tarea_inicio` | Desde qué hora trabaja en la tarea actual (fecha ISO) |
| `avance` | Porcentaje completado, de 0 a 100 |
| `tokens.entrada` / `tokens.salida` | Tokens leídos y escritos hoy |
| `tokens.limite_diario` | Límite del día, para mostrar el % usado |
| `tokens.por_hora` | Lista de hasta 12 números: tokens de cada una de las últimas horas (el último es la hora actual) |
| `completadas_hoy` | Tareas terminadas hoy |
| `activo_desde` | Desde qué hora está encendido hoy |
| `ultima_actividad` | Hora de su último reporte |
| `cola` | Lista de sus próximas tareas |
| `historial` | Lista de `{ "hora": "10:05", "texto": "..." }` |
| `modelo`, `herramientas`, `mision` | Su ficha fija (si no se envían, se usan las de la página) |

`estado.ejemplo.json` trae un bot (Bety) con todos los campos llenos como modelo.

## Chat del equipo

El botón **Chat del equipo** abre una conversación con dos tipos de canal:

- **# Equipo**: todos los agentes y tú. Ahí se ven también las conversaciones entre ellos, las tareas que se asignan y los pedidos de ayuda. Menciona a un agente con `@Nombre`.
- **Privado**: tú con un solo agente. También se abre desde su ficha con “Chatear con…”.

Botones rápidos: *¿Cómo van todos?*, *Asignar tarea* y *Convocar reunión* (los robots caminan al Meeting Room).

En **simulación**, los agentes responden solos: reparten las tareas según el tema (contenido → Bety, marketing y leads → Mark, CRM y clientes → Marcelo, ventas → Viktor, investigación → Sergio, coordinación → Sylvia), se piden ayuda y caminan a la sala del compañero.

En **vivo**, los mensajes de los agentes llegan en el campo `mensajes` de `estado.json`:

```json
"mensajes": [
  { "id": 1, "de": "@sylvia", "para": "todos", "texto": "Prioridades de hoy…", "hora": "2026-09-24T09:00:00-04:00" },
  { "id": 2, "de": "@sylvia", "para": "@contenido-madreperla", "tipo": "tarea", "estado": "aceptada", "texto": "Carrusel de Miches" },
  { "id": 3, "de": "@mark", "para": "todos", "tipo": "ayuda", "texto": "Necesito una aprobación" },
  { "id": 4, "de": "@marcelo", "para": "tu", "texto": "Mensaje privado para ti" }
]
```

- `de` / `para`: el usuario de Hermes o el nombre corto; `para` también puede ser `todos` o `tu` (privado contigo).
- `tipo`: `mensaje` (por defecto), `tarea`, `ayuda`, `sistema` o `evento` (aviso de la Sala de Eventos, ver abajo).
- `estado` (solo tareas): `pendiente`, `aceptada` o `hecha`.

Con el servidor local (*Conectado a Hermes*), lo que escribes llega a tus bots y sus respuestas aparecen en el chat. Si la página está publicada en otro lugar (*En vivo*), el chat es de solo lectura.

Las **aprobaciones** llegan en el campo `aprobaciones` de `estado.json`:

```json
"aprobaciones": [
  { "id": "1", "de": "@contenido-madreperla", "titulo": "Carrusel de Cap Cana", "detalle": "Texto del borrador…", "clase": "borrador", "estado": "pendiente", "hora": "2026-09-24T09:40:00-04:00" }
]
```

`clase` puede ser `borrador`, `propuesta` o `consulta`. `estado` puede ser `pendiente`, `aprobada` o `devuelta` (en estas dos, con `comentario`). Los bots las crean con `reportar.py --aprobacion`.

Los **eventos** de la Sala de Eventos llegan en el campo `eventos` de `estado.json`:

```json
"eventos": [
  { "id": "cal-3f9a1c0b7d2e4a51", "titulo": "Torneo de golf Bogotá",
    "inicio": "2026-09-26T08:00:00-05:00", "fin": "2026-09-26T14:00:00-05:00", "todo_el_dia": false,
    "zona": "America/Bogota", "lugar": "Club El Rincón", "descripcion": "",
    "fuente": "calendario", "avisos": ["7d", "2d"], "preparado": "2026-09-24T08:10:00-04:00" }
]
```

| Campo | Qué es |
|---|---|
| `id` | `cal-…` si viene del calendario (no cambia entre lecturas), `man-<milisegundos>` si se agregó en el hábitat, `her-<milisegundos>` si lo agendó un bot |
| `titulo` | Nombre del evento (máximo 140 caracteres) |
| `inicio` | Fecha y hora con su desfase horario, por ejemplo `2026-09-26T08:00:00-05:00`. Si es de todo el día, la fecha a las 00:00 en su zona |
| `fin` | Igual que `inicio`, o `null`. Sin fin, el evento dura 2 horas (o el día completo si es de todo el día) |
| `todo_el_dia` | `true` o `false` |
| `zona` | Zona horaria del evento, por ejemplo `America/Bogota`, o `null` si no se conoce |
| `lugar` | Texto (máximo 200 caracteres) o `null` |
| `descripcion` | Texto (máximo 1000 caracteres). Puede estar vacío |
| `fuente` | `calendario`, `manual` o `hermes` |
| `avisos` | Avisos ya enviados (ver la tabla de abajo) |
| `preparado` | Fecha de la última vez que se pidió preparar el evento, o `null` |

Los avisos van en este orden:

| Aviso | Cuándo aplica | Frase |
|---|---|---|
| `7d` | Faltan 7 días o menos (y más de 48 horas) | "Falta una semana o menos para…" |
| `2d` | Faltan 48 horas o menos (y más de 24) | "Faltan 2 días para…" |
| `1d` | Faltan 24 horas o menos (y más de 3) | "Mañana es…" (o "Hoy es…", si es más tarde ese mismo día) |
| `3h` | Faltan 3 horas o menos | "En menos de 3 horas empieza…" |
| `ahora` | Ya empezó y no ha terminado | "Ya empezó…" |
| `despues` | Ya terminó y han pasado menos de 3 días | "Terminó… Es buen momento para el seguimiento." |

Cada aviso se da una sola vez. Se toma el más urgente que aplica y, si no está en `avisos`, se envía y se anotan él y todos los anteriores. Así, un evento que aparece a un día solo avisa `1d`, no `7d` ni `2d`. Los eventos salen de la lista 3 días después de terminar.

Cada aviso llega a `mensajes` como un mensaje de tipo `evento`:

```json
{ "id": "…", "de": "sistema", "para": "todos", "tipo": "evento", "evento": "cal-3f9a1c0b7d2e4a51", "umbral": "2d",
  "texto": "Faltan 2 días para «Torneo de golf Bogotá» (sábado 26 de septiembre, 08:00 · Bogotá).", "hora": "2026-09-24T08:10:00-04:00" }
```

La fecha del texto va en español, con hora de 24 horas, en la zona del evento (o en la de Santo Domingo, si no se conoce).

Las tareas (`"tipo": "tarea"`), las aprobaciones y las presentaciones pueden llevar `"evento": "<id>"`. Así aparecen en el plan de preparación de ese evento. Los bots lo agregan con `reportar.py --evento ID`.

No pongas en `tarea` ni en los eventos datos sensibles de clientes (nombres completos, cédulas, montos): el archivo se puede ver públicamente si la página está publicada.

## Nota sobre Pluse

Pluse guarda páginas para funcionar sin conexión. Si publicas el hábitat en la misma dirección que Pluse (`…github.io/pluse/habitat/`), ese guardado puede mezclar ambas páginas. Lo más limpio es moverlo a su propio repositorio (por ejemplo `habitat`).
