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

**Conectar Hermes:** ver `puente/HERMES.md`.

## Cómo funciona

- **Sin `estado.json`** → la página entra en *Simulación*: los robots trabajan, se reúnen y se mueven solos con tareas de ejemplo.
- **Con `estado.json`** junto a `index.html` → pasa a *En vivo*: cada 15 segundos lee ese archivo y mueve a cada robot según lo que diga.

## Cómo conectar un agente real

Cada agente solo tiene que actualizar su línea en `estado.json` (copia `estado.ejemplo.json` como punto de partida):

```json
{ "id": "@contenido-madreperla", "estado": "trabajando", "tarea": "Redactando el calendario de octubre" }
```

- `id`: el usuario de Hermes del bot (`@sylvia`, `@contenido-madreperla`…) o su nombre corto (`sylvia`, `sergio`, `bety`, `mark`, `marcelo`, `viktor`).
- `estado`: `trabajando`, `pensando`, `reunion`, `inactivo` o `error` (este último hace parpadear al robot en rojo: necesita ayuda).
- `sala` (opcional): `code`, `design`, `analitica`, `libreria`, `archivo`, `ventas` o `meeting`. Si no se pone, el robot va a su propia sala (o al Meeting Room si está en reunión).
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
- `tipo`: `mensaje` (por defecto), `tarea`, `ayuda` o `sistema`.
- `estado` (solo tareas): `pendiente`, `aceptada` o `hecha`.

Lo que tú escribes en modo en vivo se queda en tu pantalla: para que llegue a los agentes reales hace falta conectar la página con ellos (siguiente paso).

No pongas en `tarea` datos sensibles de clientes (nombres completos, cédulas, montos): el archivo se puede ver públicamente si la página está publicada.

## Nota sobre Pluse

Pluse guarda páginas para funcionar sin conexión. Si publicas el hábitat en la misma dirección que Pluse (`…github.io/pluse/habitat/`), ese guardado puede mezclar ambas páginas. Lo más limpio es moverlo a su propio repositorio (por ejemplo `habitat`).
