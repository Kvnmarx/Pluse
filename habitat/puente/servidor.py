#!/usr/bin/env python3
"""
Servidor local del Hábitat de Madreperla.

- Muestra el hábitat en http://127.0.0.1:8787 (solo en esta computadora).
- Lleva tus mensajes del chat y tus decisiones de aprobación a los bots de
  Hermes (por su API local) y publica sus respuestas en el hábitat.
- Si un bot le asigna una tarea a otro con reportar.py, se la hace llegar.

Uso:
  python3 servidor.py                 abre el navegador solo
  python3 servidor.py --sin-navegador
  python3 servidor.py --puerto 8790

Necesita puente/bots.json (copia bots.ejemplo.json y completa las claves).
Solo usa la biblioteca estándar de Python: no hay que instalar nada.
"""
import argparse, json, os, re, secrets, sys, threading, time, urllib.error, urllib.request, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import reportar as R   # noqa: E402  (mismo archivo de estado, mismo bloqueo)

RAIZ = os.path.dirname(AQUI)
CONFIG = os.path.join(AQUI, 'bots.json')
TOKEN = secrets.token_urlsafe(24)          # protege los envíos contra otras páginas web
EXT_PUBLICAS = {'.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.webmanifest', '.woff2'}
MAX_CUERPO = 20000

NOMBRES_BASE = {'@sylvia': 'Sylvia', '@viktor': 'Viktor', '@ageente-de-investigacion-madreperla': 'Sergio',
                '@contenido-madreperla': 'Bety', '@mark': 'Mark', '@marcelo': 'Marcelo'}
ROLES_BASE = {'@sylvia': 'coordina al equipo', '@viktor': 'ventas', '@ageente-de-investigacion-madreperla': 'investigación',
              '@contenido-madreperla': 'contenido', '@mark': 'marketing y leads', '@marcelo': 'CRM y clientes'}

cfg = {}
modelos = {}                               # bot → nombre de modelo que anuncia su API
candados = {}                              # un mensaje a la vez por bot
reenvios = []                              # tiempos de reenvíos entre bots (límite anti-bucles)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ─────────────────────────── configuración ───────────────────────────

def cargar_config():
    global cfg
    if not os.path.exists(CONFIG):
        cfg = {'bots': {}}
        return
    with open(CONFIG, encoding='utf-8') as f:
        cfg = json.load(f)
    cfg.setdefault('bots', {})
    cfg['bots'] = {R.handle(k): v for k, v in cfg['bots'].items()}
    cfg['coordinador'] = R.handle(cfg.get('coordinador', '@sylvia'))
    for b in cfg['bots']:
        candados.setdefault(b, threading.Lock())


def nombre(bot):
    return (cfg['bots'].get(bot, {}).get('nombre')) or NOMBRES_BASE.get(bot) or bot.lstrip('@').capitalize()


def url_bot(bot):
    b = cfg['bots'][bot]
    if b.get('url'):
        return b['url'].rstrip('/')
    base = cfg.get('hermes', 'http://127.0.0.1:8642').rstrip('/')
    perfil = b.get('perfil', bot.lstrip('@'))
    return base if perfil in ('', 'default', 'principal') else f'{base}/p/{perfil}'


def http_json(url, clave, cuerpo=None, espera=30, extra=None):
    headers = {'Authorization': f'Bearer {clave}', 'Content-Type': 'application/json', **(extra or {})}
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, headers=headers, method='POST' if datos else 'GET')
    with urllib.request.urlopen(req, timeout=espera) as r:
        return json.load(r)


def modelo_de(bot):
    if bot in modelos:
        return modelos[bot]
    b = cfg['bots'][bot]
    m = b.get('modelo')
    if not m:
        try:
            lista = http_json(url_bot(bot) + '/v1/models', b.get('clave', ''), espera=10)
            m = (lista.get('data') or [{}])[0].get('id')
        except Exception:
            m = None
    modelos[bot] = m or b.get('perfil') or bot.lstrip('@')
    return modelos[bot]


# ─────────────────────────── conversación con Hermes ───────────────────────────

def instrucciones(bot, canal):
    equipo = '; '.join(f'{nombre(b)} ({b}, {ROLES_BASE.get(b, "equipo")})' for b in cfg['bots'])
    donde = ('en el canal general del equipo; todos los bots pueden leerlo' if canal == 'equipo'
             else 'en una conversación privada contigo')
    return (
        f'Este mensaje llega desde el Hábitat de Madreperla, el laboratorio 3D donde trabaja el equipo de agentes. '
        f'Te escribe María Andrea, fundadora de Madreperla Realtors, {donde}. '
        'Responde en español, en pocas frases (máximo 4), con tono profesional y cercano: es una conversación interna. '
        'Si te pide una tarea, confírmala y trabájala según tus instrucciones habituales; puedes reportar avances con reportar.py. '
        'Si necesitas su visto bueno, pídelo con reportar.py --aprobacion. '
        'Nunca envíes ni publiques nada hacia clientes sin una aprobación explícita de María Andrea, '
        'y no decidas temas legales, contractuales ni precios finales. '
        f'Equipo: {equipo}.'
    )


def con_estado(fn):
    """Ejecuta fn(data, t) con estado.json bloqueado y lo guarda."""
    with R.Bloqueo():
        data = R.leer()
        t = R.ahora()
        out = fn(data, t)
        R.guardar(data, t)
        return out


def aviso(canal, texto):
    """Mensaje del sistema dentro de un canal del chat."""
    def f(data, t):
        R.agregar_mensaje(data, 'sistema', texto, para='tu', tipo='sistema', t=t, canal=canal)
    con_estado(f)


def preguntar(bot, texto, canal, responder_a, al_terminar=None):
    """Envía `texto` al bot por su API local y publica la respuesta. Corre en su propio hilo."""
    if bot not in cfg['bots']:
        aviso(canal, f'{nombre(bot)} todavía no está conectado: falta en puente/bots.json.')
        return
    def empezar(data, t):
        ag = R.agente(data, bot, t)
        previo = (ag.get('estado'), ag.get('tarea'))
        if ag.get('estado') not in ('trabajando', 'reunion'):
            ag['estado'] = 'pensando'
        data.setdefault('escribiendo', [])
        data['escribiendo'] = [e for e in data['escribiendo'] if e.get('bot') != bot] + [{'bot': bot, 'canal': canal, 'desde': t.isoformat()}]
        return previo

    with candados[bot]:
        previo = con_estado(empezar)
        b = cfg['bots'][bot]
        cuerpo = {'model': modelo_de(bot), 'stream': False,
                  'messages': [{'role': 'system', 'content': instrucciones(bot, canal)},
                               {'role': 'user', 'content': texto}]}
        sesion = f'habitat-{bot.lstrip("@")}-{"equipo" if canal == "equipo" else "privado"}'
        respuesta, uso, error = None, {}, None
        try:
            r = http_json(url_bot(bot) + '/v1/chat/completions', b.get('clave', ''), cuerpo,
                          espera=int(cfg.get('espera_segundos', 600)), extra={'X-Hermes-Session-Id': sesion})
            respuesta = ((r.get('choices') or [{}])[0].get('message') or {}).get('content') or ''
            uso = r.get('usage') or {}
            log(f'{nombre(bot)} respondió ({uso.get("total_tokens", "?")} tokens).')
        except urllib.error.HTTPError as e:
            error = (f'La clave de {nombre(bot)} no es correcta. Revisa puente/bots.json.' if e.code in (401, 403)
                     else f'{nombre(bot)} no pudo responder (Hermes devolvió el error {e.code}).')
        except (urllib.error.URLError, ConnectionError) as e:
            error = f'No pude comunicarme con {nombre(bot)}. Revisa que el gateway de Hermes esté encendido.'
            log('Error de conexión:', e)
        except TimeoutError:
            error = f'{nombre(bot)} tardó demasiado en responder.'
        except Exception as e:                     # respuesta inesperada
            error = f'{nombre(bot)} respondió algo que no pude leer.'
            log('Error:', repr(e))

        def terminar(data, t):
            data['escribiendo'] = [e for e in data.get('escribiendo', []) if e.get('bot') != bot]
            ag = R.agente(data, bot, t)
            if ag.get('estado') == 'pensando' and previo[0] != 'pensando':
                ag['estado'] = previo[0] or 'inactivo'
            ag['ultima_actividad'] = t.isoformat()
            R.sumar_tokens(ag, uso.get('prompt_tokens', 0), uso.get('completion_tokens', 0), t)
            if respuesta and respuesta.strip():
                R.agregar_mensaje(data, bot, respuesta.strip()[:4000], para=responder_a, t=t)
            elif error:
                R.agregar_mensaje(data, 'sistema', error, para='tu', tipo='sistema', t=t,
                                  canal='equipo' if canal == 'equipo' else bot)
        con_estado(terminar)
    if respuesta and al_terminar:
        al_terminar()


def en_hilo(fn, *a, **k):
    threading.Thread(target=fn, args=a, kwargs=k, daemon=True).start()


def destinatarios(texto):
    """Bots mencionados en un mensaje del canal general (@Nombre o @usuario)."""
    encontrados = []
    for m in re.findall(r'@([\w\-áéíóúñÁÉÍÓÚÑ]+)', texto):
        m_l = m.lower()
        for b in cfg['bots']:
            if m_l in (b.lstrip('@').lower(), nombre(b).lower()) and b not in encontrados:
                encontrados.append(b)
    return encontrados


# ─────────────────────────── acciones de la página ───────────────────────────

def recibir_mensaje(cuerpo):
    texto = str(cuerpo.get('texto', '')).strip()[:2000]
    para = R.handle(str(cuerpo.get('para', 'todos')))
    if not texto:
        return 400, {'error': 'El mensaje está vacío.'}
    if para != 'todos' and para not in cfg['bots'] and para not in NOMBRES_BASE:
        return 400, {'error': 'Ese bot no existe.'}
    con_estado(lambda data, t: R.agregar_mensaje(data, 'tu', texto, para=para, t=t))
    if para == 'todos':
        bots = destinatarios(texto) or [cfg['coordinador']]
        for b in bots:
            en_hilo(preguntar, b, texto, 'equipo', 'todos')
    else:
        en_hilo(preguntar, para, texto, para, 'tu')
    return 200, {'ok': True}


def recibir_aprobacion(cuerpo):
    aid = str(cuerpo.get('id', ''))
    decision = cuerpo.get('decision')
    comentario = str(cuerpo.get('comentario', '')).strip()[:1500]
    if decision not in ('aprobada', 'devuelta'):
        return 400, {'error': 'Decisión no válida.'}
    if decision == 'devuelta' and not comentario:
        return 400, {'error': 'Para devolver, escribe qué hay que ajustar.'}

    def decidir(data, t):
        item = next((a for a in data.get('aprobaciones', []) if a.get('id') == aid), None)
        if not item or item.get('estado') != 'pendiente':
            return None
        item.update({'estado': decision, 'comentario': comentario, 'decidido': t.isoformat()})
        return dict(item)
    item = con_estado(decidir)
    if not item:
        return 409, {'error': 'Esa solicitud ya no está pendiente.'}
    bot = R.handle(item['de'])
    if decision == 'aprobada':
        texto = f'María Andrea aprobó «{item["titulo"]}» desde el Hábitat.'
    else:
        texto = f'María Andrea devolvió «{item["titulo"]}» para ajustes.'
    if comentario:
        texto += f' Comentario: {comentario}'
    texto += ' Continúa según corresponda y confírmale brevemente qué harás.'
    en_hilo(preguntar, bot, texto, bot, 'tu')
    return 200, {'ok': True}


def recibir_reunion(cuerpo):
    tema = str(cuerpo.get('tema', '')).strip()[:200] or 'Reunión convocada por María Andrea'
    minutos = max(2, min(60, int(cuerpo.get('minutos', 10) or 10)))

    def convocar(data, t):
        hasta = time.time() + minutos * 60
        for b in cfg['bots'] or NOMBRES_BASE:
            ag = R.agente(data, b, t)
            if ag.get('estado') != 'reunion':
                ag['_antes_reunion'] = {'estado': ag.get('estado'), 'tarea': ag.get('tarea', '')}
            ag.update({'estado': 'reunion', 'tarea': tema, '_reunion_hasta': hasta})
            ag.pop('sala', None)
        R.agregar_mensaje(data, 'tu', f'Convoco una reunión en el Meeting Room: {tema}.', para='todos', t=t)
    con_estado(convocar)
    if cfg['bots']:
        en_hilo(preguntar, cfg['coordinador'],
                f'María Andrea convocó una reunión en el Meeting Room del Hábitat: «{tema}». Abre la reunión con el equipo en pocas frases.',
                'equipo', 'todos')
    return 200, {'ok': True}


# ─────────────────────────── vigilante ───────────────────────────

def vigilante():
    """Cada 2 segundos: termina reuniones vencidas y reenvía tareas entre bots."""
    while True:
        time.sleep(2)
        try:
            pendientes = []

            def revisar(data):
                cambio = False
                ahora_s = time.time()
                for ag in data['agentes']:
                    if ag.get('_reunion_hasta') and ag['_reunion_hasta'] < ahora_s:
                        antes = ag.pop('_antes_reunion', {}) or {}
                        ag.pop('_reunion_hasta', None)
                        if ag.get('estado') == 'reunion':
                            ag['estado'] = antes.get('estado') or 'inactivo'
                            ag['tarea'] = antes.get('tarea', '')
                        cambio = True
                if cfg.get('reenviar_tareas', True):
                    for m in data.get('mensajes', []):
                        if (m.get('tipo') == 'tarea' and not m.get('reenviado') and m.get('de') in cfg['bots']
                                and m.get('para') in cfg['bots']):
                            m['reenviado'] = True
                            pendientes.append(dict(m))
                            cambio = True
                return cambio
            if os.path.exists(R.ESTADO):
                with R.Bloqueo():               # solo guarda si algo cambió
                    data = R.leer()
                    if revisar(data):
                        R.guardar(data)
            for m in pendientes:
                ahora_s = time.time()
                reenvios[:] = [x for x in reenvios if ahora_s - x < 600]
                if len(reenvios) >= int(cfg.get('max_reenvios_10min', 6)):
                    log('Límite de reenvíos alcanzado: la tarea queda solo en el hábitat.')
                    continue
                reenvios.append(ahora_s)
                destino, origen = m['para'], m['de']

                def aceptar(mid=m['id']):
                    def f(data, t):
                        for x in data.get('mensajes', []):
                            if x.get('id') == mid and x.get('estado') == 'pendiente':
                                x['estado'] = 'aceptada'
                    con_estado(f)
                en_hilo(preguntar, destino,
                        f'{nombre(origen)} te asignó una tarea desde el Hábitat: «{m["texto"]}». Confírmala en una frase y trabájala según tus instrucciones.',
                        'equipo', 'todos', aceptar)
        except Exception as e:
            log('Vigilante:', repr(e))


# ─────────────────────────── servidor web ───────────────────────────

class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RAIZ, **k)

    def log_message(self, fmt, *args):   # silencioso: solo errores
        if len(args) >= 2 and str(args[1])[:1] in ('4', '5'):
            log('Web:', fmt % args)

    def _host_ok(self):
        return self.headers.get('Host', '') in self.server.hosts

    def _json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def end_headers(self):
        if urlparse(self.path).path.endswith('estado.json'):
            self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {'error': 'Acceso no permitido.'})
        ruta = unquote(urlparse(self.path).path)
        if ruta == '/api/salud':
            return self._json(200, {'ok': True, 'token': TOKEN, 'coordinador': cfg.get('coordinador'),
                                    'bots': {b: True for b in cfg['bots']}})
        if ruta in ('/', ''):
            self.path = '/index.html'
            return super().do_GET()
        partes = [p for p in ruta.split('/') if p]
        ext = os.path.splitext(ruta)[1].lower()
        permitido = (ruta == '/estado.json' or (ext in EXT_PUBLICAS and 'puente' not in partes
                                                 and not any(p.startswith('.') for p in partes)))
        if not permitido:
            return self._json(404, {'error': 'No encontrado.'})
        if ruta == '/estado.json' and not os.path.exists(R.ESTADO):
            return self._json(404, {'error': 'Todavía no hay estado.'})
        return super().do_GET()

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {'error': 'Acceso no permitido.'})
        origen = self.headers.get('Origin')
        if origen and origen not in self.server.origenes:
            return self._json(403, {'error': 'Origen no permitido.'})
        if self.headers.get('X-Habitat-Token') != TOKEN:
            return self._json(403, {'error': 'Falta la llave de la sesión. Recarga la página.'})
        largo = int(self.headers.get('Content-Length') or 0)
        if largo <= 0 or largo > MAX_CUERPO:
            return self._json(413, {'error': 'Mensaje demasiado largo.'})
        try:
            cuerpo = json.loads(self.rfile.read(largo).decode('utf-8'))
            assert isinstance(cuerpo, dict)
        except Exception:
            return self._json(400, {'error': 'Formato no válido.'})
        rutas = {'/api/mensaje': recibir_mensaje, '/api/aprobacion': recibir_aprobacion, '/api/reunion': recibir_reunion}
        fn = rutas.get(urlparse(self.path).path)
        if not fn:
            return self._json(404, {'error': 'No encontrado.'})
        try:
            codigo, resp = fn(cuerpo)
        except RuntimeError as e:
            codigo, resp = 503, {'error': str(e)}
        return self._json(codigo, resp)


def preparar_estado():
    """Crea estado.json con los bots configurados para que la página arranque en vivo."""
    def f(data, t):
        for b in (cfg['bots'] or NOMBRES_BASE):
            R.agente(data, b, t)
        data['escribiendo'] = []
    con_estado(f)


def main():
    ap = argparse.ArgumentParser(description='Servidor local del Hábitat de Madreperla.')
    ap.add_argument('--puerto', type=int, default=int(os.environ.get('HABITAT_PUERTO', 8787)))
    ap.add_argument('--sin-navegador', action='store_true')
    a = ap.parse_args()

    cargar_config()
    preparar_estado()
    srv = ThreadingHTTPServer(('127.0.0.1', a.puerto), Manejador)
    srv.hosts = {f'127.0.0.1:{a.puerto}', f'localhost:{a.puerto}'}
    srv.origenes = {f'http://127.0.0.1:{a.puerto}', f'http://localhost:{a.puerto}'}
    threading.Thread(target=vigilante, daemon=True).start()

    url = f'http://127.0.0.1:{a.puerto}/'
    print('\n  Hábitat de Madreperla')
    print(f'  Abierto en {url}  (solo en esta computadora)')
    if cfg['bots']:
        print('  Bots conectados: ' + ', '.join(f'{nombre(b)} ({b})' for b in cfg['bots']))
    else:
        print('  Aviso: falta puente/bots.json. El hábitat se ve, pero los mensajes no llegarán a Hermes.')
    print('  Para cerrarlo, presiona Ctrl+C.\n')
    if not a.sin_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n  Hábitat cerrado.')


if __name__ == '__main__':
    main()
