# Laboratorio de agentes · María Andrea

Laboratorio personal donde agentes de IA trabajan en proyectos distintos: código, trabajo y vida personal. Tiene el mismo estilo y funciones que el Hábitat de Madreperla (`../habitat`), que sigue igual y por separado.

## Áreas y agentes de ejemplo

El laboratorio es una nave oscura con luces de neón. Cada área es una zona del piso de su color, pegada a la siguiente y con borde de neón; no hay paredes entre ellas. Cada agente trabaja en un círculo de luz frente a su consola, con una terminal flotante que muestra lo que está haciendo, y el nombre de cada área va en un cartel en el piso. Junto a los muros están las máquinas gigantes (supercomputadora, robot en construcción, tubos de químicos, cintas transportadoras), en la Agenda hay un teletransportador y todas las áreas se conectan con el cerebro central sobre la Sala central. Los robots tienen casco con visor negro y ojos de luz, cuerpo redondo, brazos con manos y piernas.

| Área | Agente | Proyecto |
|---|---|---|
| Sala central | Mentor | Coordina el laboratorio y las juntas |
| Code Lab | Nova | Pluse (app de tareas y hábitos) |
| Code Lab | Kai | Hábitats de agentes |
| Estudio | Iris | Marca personal y contenido |
| Observatorio | Atlas | Finanzas personales |
| Biblioteca | Sage | Aprendizaje e investigación |
| Archivo | Orden | Vida personal y trámites |
| Ala Madreperla | Perla | Enlace con el hábitat de Madreperla |
| Puesto de mando | María Andrea | Desde donde apruebas todo |
| Núcleo de datos | (libre) | Servidores y automatizaciones |
| Invernadero | (libre) | Salud y bienestar |

Los agentes, proyectos y textos son de ejemplo. Para cambiarlos, edita al principio de `index.html` los bloques `ROOMS` (áreas), `AGENTS` (agentes), `PROFILE` (misión de cada uno) y `SIM_TASKS` (tareas), y más abajo `FRENTES_SIM` (frentes y plazos).

## Conectar agentes reales

Funciona igual que el hábitat de Madreperla: los agentes reportan con un `estado.json` junto a la página (ver `../habitat/LEEME.md` y `../habitat/puente/`).
