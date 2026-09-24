# Hábitat de agentes · Madreperla

Laboratorio 3D donde viven los seis agentes de IA. Cada robot tiene su color y su sala.

| Robot  | Color    | Sala          | Función                       |
|--------|----------|---------------|-------------------------------|
| Byte   | Cian     | Code Lab      | Código y automatizaciones     |
| Pixel  | Magenta  | Design Room   | Diseño y piezas visuales      |
| Metric | Ámbar    | Analítica     | Datos y métricas              |
| Folio  | Verde    | Librería      | Investigación y lectura       |
| Arca   | Violeta  | Archivo       | Documentos archivados         |
| Nexo   | Coral    | Meeting Room  | Coordina al equipo            |

## Cómo funciona

- **Sin `estado.json`** → la página entra en *Simulación*: los robots trabajan, se reúnen y se mueven solos con tareas de ejemplo.
- **Con `estado.json`** junto a `index.html` → pasa a *En vivo*: cada 15 segundos lee ese archivo y mueve a cada robot según lo que diga.

## Cómo conectar un agente real

Cada agente solo tiene que actualizar su línea en `estado.json` (copia `estado.ejemplo.json` como punto de partida):

```json
{ "id": "byte", "estado": "trabajando", "tarea": "Actualizando la web de propiedades" }
```

- `id`: byte, pixel, metric, folio, arca o nexo.
- `estado`: `trabajando`, `pensando`, `reunion`, `inactivo` o `error` (este último hace parpadear al robot en rojo: necesita ayuda).
- `sala` (opcional): `code`, `design`, `analitica`, `libreria`, `archivo` o `meeting`. Si no se pone, el robot va a su propia sala (o al Meeting Room si está en reunión).
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

`estado.ejemplo.json` trae un agente (Byte) con todos los campos llenos como modelo.

## Chat del equipo

El botón **Chat del equipo** abre una conversación con dos tipos de canal:

- **# Equipo**: todos los agentes y tú. Ahí se ven también las conversaciones entre ellos, las tareas que se asignan y los pedidos de ayuda. Menciona a un agente con `@Nombre`.
- **Privado**: tú con un solo agente. También se abre desde su ficha con “Chatear con…”.

Botones rápidos: *¿Cómo van todos?*, *Asignar tarea* y *Convocar reunión* (los robots caminan al Meeting Room).

En **simulación**, los agentes responden solos: reparten las tareas según el tema (diseño → Pixel, datos → Metric, web → Byte, investigación → Folio, documentos → Arca, coordinación → Nexo), se piden ayuda y caminan a la sala del compañero.

En **vivo**, los mensajes de los agentes llegan en el campo `mensajes` de `estado.json`:

```json
"mensajes": [
  { "id": 1, "de": "nexo", "para": "todos", "texto": "Prioridades de hoy…", "hora": "2026-09-24T09:00:00-04:00" },
  { "id": 2, "de": "nexo", "para": "pixel", "tipo": "tarea", "estado": "aceptada", "texto": "Carrusel de Miches" },
  { "id": 3, "de": "byte", "para": "todos", "tipo": "ayuda", "texto": "Necesito una aprobación" },
  { "id": 4, "de": "arca", "para": "tu", "texto": "Mensaje privado para ti" }
]
```

- `para`: `todos`, el id de otro agente, o `tu` (privado contigo).
- `tipo`: `mensaje` (por defecto), `tarea`, `ayuda` o `sistema`.
- `estado` (solo tareas): `pendiente`, `aceptada` o `hecha`.

Lo que tú escribes en modo en vivo se queda en tu pantalla: para que llegue a los agentes reales hace falta conectar la página con ellos (siguiente paso).

No pongas en `tarea` datos sensibles de clientes (nombres completos, cédulas, montos): el archivo se puede ver públicamente si la página está publicada.

## Nota sobre Pluse

Pluse guarda páginas para funcionar sin conexión. Si publicas el hábitat en la misma dirección que Pluse (`…github.io/pluse/habitat/`), ese guardado puede mezclar ambas páginas. Lo más limpio es moverlo a su propio repositorio (por ejemplo `habitat`).
