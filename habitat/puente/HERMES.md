# Conectar los bots de Hermes con el Hábitat

Hermes corre en tu computadora. Cada bot avisa lo que hace ejecutando `reportar.py`. Ese script actualiza `estado.json` y lo sube a GitHub. La página del hábitat lee ese archivo cada 15 segundos y mueve a los robots.

## 1. Preparar la carpeta (una sola vez)

1. En tu computadora, descarga el repositorio `habitat` con GitHub Desktop o con:
   ```
   git clone https://github.com/<tu-usuario>/habitat.git
   ```
2. Comprueba que funciona. Desde la carpeta `habitat`, ejecuta:
   ```
   python3 puente/reportar.py --bot @sylvia --estado trabajando --tarea "Probando la conexión"
   ```
   Si ves `Listo: @sylvia reportado.` y en GitHub aparece un cambio en `estado.json`, ya está.

## 2. Instrucción para cada bot

Pega este texto en las instrucciones de cada bot de Hermes. Cambia `@usuario-del-bot` por el suyo y la ruta por la de tu carpeta:

```
Reporta tu trabajo al Hábitat de Madreperla con la terminal:

  python3 /RUTA/habitat/puente/reportar.py --bot @usuario-del-bot [opciones]

- Al empezar una tarea:   --estado trabajando --tarea "texto corto"
- Si avanzas:             --avance 50
- Al terminarla:          --terminada
- Si esperas aprobación:  --estado error --tarea "Qué necesitas"
- Si estás libre:         --estado inactivo
- Para hablar al equipo:  --mensaje "texto" --para todos
- Para hablar a otro bot: --mensaje "texto" --para @otro-bot
- Para asignar una tarea: --mensaje "tarea" --tarea-para @otro-bot
- Tokens usados:          --tokens-entrada N --tokens-salida N

Textos cortos y profesionales. Nunca incluyas datos sensibles de clientes
(cédulas, cuentas, montos, teléfonos): el archivo puede ser público.
```

## 3. Usuarios de cada bot

| Bot | Usuario |
|---|---|
| Sylvia | `@sylvia` |
| Viktor | `@viktor` |
| Sergio | `@ageente-de-investigacion-madreperla` |
| Bety | `@contenido-madreperla` |
| Mark | `@mark` |
| Marcelo | `@marcelo` |

## Límites de esta primera versión

- Lo que tú escribes en el chat de la página todavía no les llega a los bots de Hermes. Por ahora, háblales desde Hermes y ellos responden en el hábitat con `--mensaje`.
- Si la página está publicada con GitHub Pages en un repositorio público, `estado.json` también es público. Por eso la regla de no poner datos de clientes.
- Si Hermes no informa los tokens, la ficha muestra 0. Si Hermes o ChatGPT te dan el consumo, pásalo con `--tokens-entrada` y `--tokens-salida`.
