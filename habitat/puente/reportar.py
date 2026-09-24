#!/usr/bin/env python3
"""
Puente Hermes → Hábitat de Madreperla.

Cada bot de Hermes ejecuta este script cuando empieza, avanza o termina una
tarea, cuando quiere decir algo en el chat del equipo o cuando necesita tu
aprobación. El script actualiza estado.json, el archivo que lee el hábitat.

Ejemplos:
  python3 reportar.py --bot @mark --estado trabajando --tarea "Midiendo leads de la semana" --avance 40
  python3 reportar.py --bot @sylvia --mensaje "Prioridades de hoy: leads y calendario" --para todos
  python3 reportar.py --bot @sylvia --tarea-para @contenido-madreperla --mensaje "Calendario de octubre"
  python3 reportar.py --bot @contenido-madreperla --aprobacion "Carrusel de Cap Cana" --detalle "Texto del borrador…"
  python3 reportar.py --bot @mark --presentar "Leads de la semana" --formato dashboard --archivo leads.json
  python3 reportar.py --bot @contenido-madreperla --presentar "Calendario de octubre" --formato slides --archivo calendario.md
  python3 reportar.py --bot @mark --tokens-entrada 1200 --tokens-salida 300
  python3 reportar.py --bot @marcelo --estado inactivo --subir

Por defecto todo queda en esta computadora. Con --subir, además se sube a
GitHub (solo hace falta si publicas el hábitat con GitHub Pages).

No escribas datos sensibles de clientes (cédulas, cuentas, montos, teléfonos).
"""
import argparse, datetime as dt, json, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(os.path.dirname(AQUI), 'estado.json')
BLOQUEO = ESTADO + '.lock'
ESTADOS = ['trabajando', 'pensando', 'reunion', 'inactivo', 'error']
SALAS = ['code', 'design', 'analitica', 'libreria', 'archivo', 'ventas', 'meeting']
CLASES = ['borrador', 'propuesta', 'consulta']
MAX_MENSAJES = 200
MAX_APROBACIONES = 60
MAX_PRESENTACIONES = 30
FORMATOS = ['slides', 'documento', 'dashboard']
MAX_HISTORIAL = 8


def ahora():
    return dt.datetime.now().astimezone()


def handle(nombre):
    """Normaliza un usuario de Hermes: 'mark' → '@mark'. Deja 'todos' y 'tu' tal cual."""
    nombre = (nombre or '').strip()
    if nombre in ('todos', 'tu', 'sistema'):
        return nombre
    return nombre if nombre.startswith('@') else '@' + nombre


class Bloqueo:
    """Evita que dos procesos escriban el archivo al mismo tiempo."""
    def __enter__(self):
        for _ in range(150):
            try:
                self.fd = os.open(BLOQUEO, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(BLOQUEO) > 30:   # bloqueo abandonado
                        os.remove(BLOQUEO)
                except FileNotFoundError:
                    pass
                time.sleep(0.2)
        raise RuntimeError('No pude tomar estado.json: otro proceso lo está usando. Intenta de nuevo.')

    def __exit__(self, *a):
        os.close(self.fd)
        try:
            os.remove(BLOQUEO)
        except FileNotFoundError:
            pass


def leer():
    if not os.path.exists(ESTADO):
        return {'actualizado': None, 'agentes': [], 'mensajes': [], 'aprobaciones': []}
    with open(ESTADO, encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('agentes', [])
    data.setdefault('mensajes', [])
    data.setdefault('aprobaciones', [])
    return data


def guardar(data, t=None):
    data['actualizado'] = (t or ahora()).isoformat()
    data['mensajes'] = data.get('mensajes', [])[-MAX_MENSAJES:]
    data['aprobaciones'] = data.get('aprobaciones', [])[-MAX_APROBACIONES:]
    data['presentaciones'] = data.get('presentaciones', [])[-MAX_PRESENTACIONES:]
    tmp = ESTADO + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ESTADO)


def agente(data, bot, t=None):
    """Devuelve la ficha del bot (la crea si no existe) con los contadores del día al día."""
    t = t or ahora()
    ag = next((x for x in data['agentes'] if x.get('id') == bot), None)
    if ag is None:
        ag = {'id': bot, 'estado': 'inactivo', 'tarea': ''}
        data['agentes'].append(ag)
    hoy = t.strftime('%Y-%m-%d')
    if ag.get('_dia') != hoy:              # los contadores se reinician solos al cambiar de fecha
        ag.update({'_dia': hoy, 'completadas_hoy': 0, 'activo_desde': t.isoformat(),
                   'tokens': {**{k: v for k, v in ag.get('tokens', {}).items() if k == 'limite_diario'},
                              'entrada': 0, 'salida': 0, 'por_hora': []},
                   '_horas': {}})
    return ag


def sumar_tokens(ag, entrada, salida, t=None):
    t = t or ahora()
    if not (entrada or salida):
        return
    tk = ag.setdefault('tokens', {})
    tk['entrada'] = tk.get('entrada', 0) + int(entrada or 0)
    tk['salida'] = tk.get('salida', 0) + int(salida or 0)
    hora = t.strftime('%Y-%m-%dT%H')
    horas = ag.setdefault('_horas', {})
    horas[hora] = horas.get(hora, 0) + int(entrada or 0) + int(salida or 0)
    ultimas = [(t - dt.timedelta(hours=h)).strftime('%Y-%m-%dT%H') for h in range(11, -1, -1)]
    tk['por_hora'] = [horas.get(h, 0) for h in ultimas]
    ag['_horas'] = {h: horas[h] for h in ultimas if h in horas}


def nuevo_id(t, quien):
    return f'{int(t.timestamp() * 1000)}-{quien.lstrip("@")}'


def agregar_mensaje(data, de, texto, para='todos', tipo='mensaje', t=None, **extra):
    t = t or ahora()
    m = {'id': nuevo_id(t, de), 'de': de, 'para': para, 'tipo': tipo, 'texto': texto, 'hora': t.isoformat(), **extra}
    data.setdefault('mensajes', []).append(m)
    return m


def agregar_aprobacion(data, de, titulo, detalle='', clase='borrador', t=None):
    t = t or ahora()
    a = {'id': nuevo_id(t, de), 'de': de, 'titulo': titulo, 'detalle': detalle, 'clase': clase,
         'estado': 'pendiente', 'hora': t.isoformat()}
    data.setdefault('aprobaciones', []).append(a)
    return a


def leer_presentacion(formato, texto):
    """Convierte el contenido a la forma que muestra el hábitat.

    - JSON: se usa tal cual (slides / secciones / kpis / series).
    - slides en texto: diapositivas separadas por una línea '---'; la línea que
      empieza con '#' es el título y las que empiezan con '-' o '*' son puntos.
    - documento en texto: cada '#' o '##' abre una sección con su texto.
    """
    texto = (texto or '').strip()
    if texto.startswith('{'):
        return json.loads(texto)
    if formato == 'dashboard':
        raise ValueError('Un dashboard necesita contenido en JSON con "kpis" y "series".')
    if formato == 'slides':
        slides = []
        for bloque in [b.strip() for b in texto.split('\n---') if b.strip()]:
            s = {'titulo': '', 'puntos': [], 'nota': ''}
            for linea in bloque.splitlines():
                l = linea.strip()
                if not l or l == '---':
                    continue
                if l.startswith('#') and not s['titulo']:
                    s['titulo'] = l.lstrip('#').strip()
                elif l[:2] in ('- ', '* '):
                    s['puntos'].append(l[2:].strip())
                elif not s['titulo']:
                    s['titulo'] = l
                else:
                    s['nota'] = (s['nota'] + ' ' + l).strip()
            slides.append(s)
        return {'slides': slides}
    secciones, actual = [], None
    for linea in texto.splitlines():
        if linea.strip().startswith('#'):
            actual = {'titulo': linea.strip().lstrip('#').strip(), 'texto': ''}
            secciones.append(actual)
        else:
            if actual is None:
                actual = {'titulo': '', 'texto': ''}
                secciones.append(actual)
            actual['texto'] = (actual['texto'] + '\n' + linea).strip('\n')
    return {'secciones': [x for x in secciones if x['titulo'] or x['texto'].strip()]}


def agregar_presentacion(data, de, titulo, formato, contenido, t=None):
    t = t or ahora()
    for x in data.setdefault('presentaciones', []):
        x['activa'] = False                          # solo una en pantalla a la vez
    pr = {'id': nuevo_id(t, de), 'de': de, 'titulo': titulo, 'tipo': formato, 'hora': t.isoformat(), 'activa': True}
    for k in ('slides', 'secciones', 'kpis', 'series'):
        if k in contenido:
            pr[k] = contenido[k]
    data['presentaciones'].append(pr)
    agregar_mensaje(data, de, titulo, para='todos', tipo='presentacion', t=t, ref=pr['id'])
    return pr


def git(*args):
    return subprocess.run(['git', '-C', os.path.dirname(ESTADO), *args], capture_output=True, text=True)


def subir(bot):
    if git('rev-parse', '--is-inside-work-tree').returncode != 0:
        print('Aviso: la carpeta no es un repositorio de git; estado.json quedó solo en esta computadora.')
        return
    git('add', '-f', 'estado.json')
    if git('diff', '--cached', '--quiet').returncode == 0:
        return
    git('commit', '-m', f'Reporte de {bot}')
    r = None
    for intento in range(3):
        git('pull', '--rebase', '--autostash')
        r = git('push')
        if r.returncode == 0:
            return
        time.sleep(2 * (intento + 1))
    print('Aviso: no pude subir el reporte a GitHub. Se subirá con el próximo reporte.\n' + r.stderr.strip())


def main():
    ap = argparse.ArgumentParser(description='Reporta el estado de un bot de Hermes al Hábitat de Madreperla.')
    ap.add_argument('--bot', required=True, help='Usuario del bot en Hermes, por ejemplo @mark')
    ap.add_argument('--estado', choices=ESTADOS)
    ap.add_argument('--tarea', help='Qué está haciendo ahora (texto corto)')
    ap.add_argument('--avance', type=int, help='Porcentaje completado, de 0 a 100')
    ap.add_argument('--sala', choices=SALAS, help='Sala a la que va (opcional)')
    ap.add_argument('--terminada', action='store_true', help='Marca la tarea actual como terminada')
    ap.add_argument('--siguiente', action='append', help='Agrega una tarea a su lista (se puede repetir)')
    ap.add_argument('--tokens-entrada', type=int, default=0)
    ap.add_argument('--tokens-salida', type=int, default=0)
    ap.add_argument('--limite-diario', type=int)
    ap.add_argument('--modelo', help='Por ejemplo: Hermes Agent · ChatGPT')
    ap.add_argument('--mensaje', help='Mensaje para el chat del equipo')
    ap.add_argument('--para', default='todos', help='todos, tu, o el usuario de otro bot')
    ap.add_argument('--tipo', choices=['mensaje', 'ayuda'], default='mensaje')
    ap.add_argument('--tarea-para', help='Asigna el --mensaje como tarea a este bot')
    ap.add_argument('--aprobacion', help='Pide la aprobación de María Andrea: título corto')
    ap.add_argument('--detalle', default='', help='Texto completo de lo que hay que aprobar')
    ap.add_argument('--clase', choices=CLASES, default='borrador', help='borrador, propuesta o consulta')
    ap.add_argument('--presentar', help='Presenta un trabajo en la pantalla del Meeting Room: título')
    ap.add_argument('--formato', choices=FORMATOS, default='slides', help='slides, documento o dashboard')
    ap.add_argument('--archivo', help='Archivo con el contenido (texto o JSON)')
    ap.add_argument('--contenido', help='Contenido directo (texto o JSON), si no usas --archivo')
    ap.add_argument('--terminar-presentacion', action='store_true', help='Apaga la pantalla del Meeting Room')
    ap.add_argument('--subir', action='store_true', help='Además, sube estado.json a GitHub')
    ap.add_argument('--sin-subir', action='store_true', help=argparse.SUPPRESS)   # compatibilidad
    a = ap.parse_args()

    bot = handle(a.bot)
    t = ahora()
    contenido = None
    if a.presentar:
        try:
            crudo = open(a.archivo, encoding='utf-8').read() if a.archivo else (a.contenido or '')
            contenido = leer_presentacion(a.formato, crudo)
        except (OSError, ValueError) as e:
            sys.exit(f'No pude leer el contenido de la presentación: {e}')

    try:
        with Bloqueo():
            data = leer()
            ag = agente(data, bot, t)

            if a.terminada and ag.get('tarea'):
                ag['completadas_hoy'] = ag.get('completadas_hoy', 0) + 1
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Terminó: ' + ag['tarea']})
                ag['tarea'], ag['avance'] = '', None

            if a.tarea is not None and a.tarea != ag.get('tarea'):
                ag['tarea'] = a.tarea
                ag['tarea_inicio'] = t.isoformat()
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Empezó: ' + a.tarea})
                ag['cola'] = [c for c in ag.get('cola', []) if c != a.tarea]
            if a.estado:
                ag['estado'] = a.estado
            if a.avance is not None:
                ag['avance'] = max(0, min(100, a.avance))
            if a.sala:
                ag['sala'] = a.sala
            elif a.estado:
                ag.pop('sala', None)
            if a.siguiente:
                ag['cola'] = (ag.get('cola', []) + a.siguiente)[-5:]
            if a.modelo:
                ag['modelo'] = a.modelo
            if a.limite_diario:
                ag.setdefault('tokens', {})['limite_diario'] = a.limite_diario
            sumar_tokens(ag, a.tokens_entrada, a.tokens_salida, t)

            if a.mensaje:
                if a.tarea_para:
                    destino = handle(a.tarea_para)
                    agregar_mensaje(data, bot, a.mensaje, para=destino, tipo='tarea', t=t, estado='pendiente')
                    otro = next((x for x in data['agentes'] if x.get('id') == destino), None)
                    if otro is not None:
                        otro['cola'] = (otro.get('cola', []) + [a.mensaje])[-5:]
                else:
                    agregar_mensaje(data, bot, a.mensaje, para=handle(a.para), tipo=a.tipo, t=t)

            if a.presentar:
                agregar_presentacion(data, bot, a.presentar, a.formato, contenido, t)
                ag['estado'], ag['sala'] = 'reunion', 'meeting'
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Presentó: ' + a.presentar})
            if a.terminar_presentacion:
                for x in data.get('presentaciones', []):
                    x['activa'] = False

            if a.aprobacion:
                agregar_aprobacion(data, bot, a.aprobacion, a.detalle, a.clase, t)
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Pidió aprobación: ' + a.aprobacion})

            ag['historial'] = ag.get('historial', [])[:MAX_HISTORIAL]
            ag['ultima_actividad'] = t.isoformat()
            guardar(data, t)
    except RuntimeError as e:
        sys.exit(str(e))

    if a.subir:
        subir(bot)
    print(f'Listo: {bot} reportado.')


if __name__ == '__main__':
    main()
