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

No pongas en `tarea` datos sensibles de clientes (nombres completos, cédulas, montos): el archivo se puede ver públicamente si la página está publicada.

## Nota sobre Pluse

Pluse guarda páginas para funcionar sin conexión. Si publicas el hábitat en la misma dirección que Pluse (`…github.io/pluse/habitat/`), ese guardado puede mezclar ambas páginas. Lo más limpio es moverlo a su propio repositorio (por ejemplo `habitat`).
