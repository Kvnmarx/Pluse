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

Sala de Eventos:
  python3 reportar.py --bot @sylvia --evento-nuevo "Torneo de golf Bogotá" --fecha 2026-09-26T08:00 --zona America/Bogota --lugar "Club El Rincón"
  python3 reportar.py --bot @sylvia --evento-nuevo "Feria inmobiliaria" --fecha 2026-10-03 --fin 2026-10-04
  python3 reportar.py --bot @sylvia --tarea-para @contenido-madreperla --mensaje "Borrador de invitación al torneo" --evento her-1790000000000
  python3 reportar.py --bot @contenido-madreperla --aprobacion "Invitación al torneo" --detalle "Texto…" --evento her-1790000000000
  python3 reportar.py --bot @sylvia --presentar "Briefing del torneo" --formato documento --archivo briefing.md --evento her-1790000000000

  --fecha acepta 2026-09-26T08:00 (hora de Santo Domingo, o de --zona si la
  indicas), 2026-09-26T08:00:00-05:00 (con desfase) o 2026-09-26 (todo el día).
  El script muestra el id del evento; úsalo con --evento para vincular tareas,
  aprobaciones y presentaciones.

Por defecto todo queda en esta computadora. Con --subir, además se sube a
GitHub (solo hace falta si publicas el hábitat con GitHub Pages).

Leads y correos (Mark):
  python3 reportar.py --bot @mark --inventario        muestra la hoja «Inventario de proyectos»
  python3 reportar.py --bot @mark --sitio             muestra el texto de madreperlarealtors.com
  python3 reportar.py --bot @mark --leads             muestra los leads registrados
  python3 reportar.py --bot @mark --perfil            muestra el perfil de lead compatible y las reglas
  python3 reportar.py --bot @mark --lead "Ana Pérez" --email ana@correo.com --pais Colombia --interes "Villa en Cap Cana" --origen "Formulario del sitio" --puntaje 4
  python3 reportar.py --bot @ageente-de-investigacion-madreperla --lead "Dr. Luis Gómez" --cargo "Cirujano, socio de clínica" --email contacto@clinica.com --pais "Estados Unidos" --fuente https://clinica.com/equipo --motivo "Publicó sobre retiro en el Caribe" --puntaje 4
  python3 reportar.py --bot @mark --lead "Dr. Luis Gómez" --email contacto@clinica.com --con-permiso   si respondió o dio su permiso
  python3 reportar.py --bot @mark --correo-para "contacto@clinica.com" --asunto "A conversation about the Caribbean" --idioma en --archivo correo.txt
  python3 reportar.py --bot @mark --no-contactar ana@correo.com   si alguien pide no recibir más correos

  Primer correo a un prospecto encontrado en internet: solo si su país está en
  bots.json › leads › primer_contacto (o si dio su permiso). Lleva al pie la dirección
  física de la oficina y el aviso de comunicación comercial.
  python3 reportar.py --bot @mark --correo-para "Ana Pérez <ana@correo.com>" --asunto "Villas frente al mar en Cap Cana" --archivo correo.txt

  El texto del correo es simple: línea en blanco = párrafo nuevo, '## ' = subtítulo,
  '- ' = lista, '**texto**' = negrita, y una línea '[Agendar una conversación](https://…)'
  se convierte en botón. El hábitat le da la identidad de Madreperla y te lo deja en
  Aprobaciones con la vista previa. Nadie lo envía hasta que lo apruebes.
  Los leads y los correos se guardan en puente/privado.json: nunca se suben a GitHub.

No escribas datos sensibles de clientes (cédulas, cuentas, montos, teléfonos).
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import correos as C   # noqa: E402
try:
    from zoneinfo import ZoneInfo
except ImportError:                        # Python sin zoneinfo: se usan desfases fijos
    ZoneInfo = None

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(os.path.dirname(AQUI), 'estado.json')
BLOQUEO = ESTADO + '.lock'
ESTADOS = ['trabajando', 'pensando', 'reunion', 'inactivo', 'error']
SALAS = ['code', 'design', 'analitica', 'libreria', 'archivo', 'ventas', 'meeting', 'eventos']
CLASES = ['borrador', 'propuesta', 'consulta', 'correo']
MAX_MENSAJES = 200
MAX_APROBACIONES = 60
MAX_PRESENTACIONES = 30
FORMATOS = ['slides', 'documento', 'dashboard']
MAX_HISTORIAL = 8
MAX_EVENTOS = 80
UMBRALES = ['7d', '2d', '1d', '3h', 'ahora', 'despues']     # del más lejano al más reciente
FUENTES = {'calendario': 'cal', 'manual': 'man', 'hermes': 'her'}
ZONA_LOCAL = 'America/Santo_Domingo'
# Sin base de zonas (p. ej. Windows sin tzdata): zonas sin horario de verano con su desfase; las demás, -04:00.
DESFASES_FIJOS = {'America/Santo_Domingo': -4, 'America/Puerto_Rico': -4, 'America/Caracas': -4,
                  'America/Bogota': -5, 'America/Lima': -5, 'America/Panama': -5, 'UTC': 0, 'Etc/UTC': 0}
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
         'octubre', 'noviembre', 'diciembre']
CIUDADES = {'Bogota': 'Bogotá', 'Mexico_City': 'Ciudad de México', 'New_York': 'Nueva York', 'Panama': 'Panamá',
            'Sao_Paulo': 'São Paulo', 'Havana': 'La Habana', 'Puerto_Rico': 'San Juan', 'London': 'Londres'}
FRASES = {
    '7d': 'Falta una semana o menos para «{titulo}» ({fecha}).',
    '2d': 'Faltan 2 días para «{titulo}» ({fecha}).',
    '1d': 'Mañana es «{titulo}» ({fecha}).',
    '3h': 'En menos de 3 horas empieza «{titulo}» ({fecha}).',
    'ahora': 'Ya empezó «{titulo}» ({fecha}).',
    'despues': 'Terminó «{titulo}» ({fecha}). Es buen momento para el seguimiento.',
}


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
        return {'actualizado': None, 'agentes': [], 'mensajes': [], 'aprobaciones': [], 'eventos': []}
    with open(ESTADO, encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('agentes', [])
    data.setdefault('mensajes', [])
    data.setdefault('aprobaciones', [])
    if not isinstance(data.get('eventos'), list):
        data['eventos'] = []
    return data


def guardar(data, t=None):
    t = t or ahora()
    data['actualizado'] = t.isoformat()
    data['mensajes'] = data.get('mensajes', [])[-MAX_MENSAJES:]
    data['aprobaciones'] = data.get('aprobaciones', [])[-MAX_APROBACIONES:]
    data['presentaciones'] = data.get('presentaciones', [])[-MAX_PRESENTACIONES:]
    data['eventos'] = recortar_eventos(data.get('eventos'), t)
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


def agregar_aprobacion(data, de, titulo, detalle='', clase='borrador', t=None, evento=None, **extra):
    t = t or ahora()
    a = {'id': nuevo_id(t, de), 'de': de, 'titulo': titulo, 'detalle': detalle, 'clase': clase,
         'estado': 'pendiente', 'hora': t.isoformat(), **extra}
    if evento:
        a['evento'] = evento
    data.setdefault('aprobaciones', []).append(a)
    return a


def correo_resumen(correo):
    """Lo que queda en estado.json de un correo: sin destinatario ni texto completo."""
    return 'Correo con la identidad de Madreperla, listo para revisar. La vista previa se abre desde el servidor local.'


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


def agregar_presentacion(data, de, titulo, formato, contenido, t=None, evento=None):
    t = t or ahora()
    for x in data.setdefault('presentaciones', []):
        x['activa'] = False                          # solo una en pantalla a la vez
    pr = {'id': nuevo_id(t, de), 'de': de, 'titulo': titulo, 'tipo': formato, 'hora': t.isoformat(), 'activa': True}
    for k in ('slides', 'secciones', 'kpis', 'series'):
        if k in contenido:
            pr[k] = contenido[k]
    vinculo = {'evento': evento} if evento else {}
    pr.update(vinculo)
    data['presentaciones'].append(pr)
    agregar_mensaje(data, de, titulo, para='todos', tipo='presentacion', t=t, ref=pr['id'], **vinculo)
    return pr


# ─────────────────────────── fechas y eventos ───────────────────────────

def zona_tz(nombre=None):
    """Zona horaria por su nombre IANA (Santo Domingo si no se indica). Si no se puede cargar, desfase fijo."""
    nombre = nombre or ZONA_LOCAL
    if ZoneInfo is not None:
        try:
            return ZoneInfo(nombre)
        except Exception:
            pass
    return dt.timezone(dt.timedelta(hours=DESFASES_FIJOS.get(nombre, -4)))


def zona_conocida(nombre):
    if not nombre:
        return False
    if ZoneInfo is not None:
        try:
            ZoneInfo(nombre)
            return True
        except Exception:
            pass
    return nombre in DESFASES_FIJOS


FECHA_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:[.,]\d+)?)?)?'
                      r'\s*(Z|[+-]\d{2}(?::?\d{2})?)?$', re.I)


def leer_fecha(valor, zona=None):
    """Texto ISO 8601 → (fecha con zona, solo_fecha). Sin desfase se interpreta en `zona` (o Santo Domingo)."""
    if isinstance(valor, dt.datetime):
        return (valor if valor.tzinfo else valor.replace(tzinfo=zona_tz(zona))), False
    m = FECHA_RE.match(str(valor or '').strip())
    if not m:
        raise ValueError('fecha no válida')
    a, me, d, h, mi, s, desfase = m.groups()
    if desfase is None:
        tz = zona_tz(zona)
    elif desfase.upper() == 'Z':
        tz = dt.timezone.utc
    else:
        cifras = desfase[1:].replace(':', '')
        delta = dt.timedelta(hours=int(cifras[:2]), minutes=int(cifras[2:] or 0))
        tz = dt.timezone(-delta if desfase[0] == '-' else delta)
    return dt.datetime(int(a), int(me), int(d), int(h or 0), int(mi or 0), int(s or 0), tzinfo=tz), h is None


def iso(d):
    return d.isoformat(timespec='seconds')


def limites(ev):
    """(inicio, fin) de un evento. Sin fin: 2 horas después del inicio, o el fin del día si es de todo el día."""
    ini = leer_fecha(ev.get('inicio'))[0]
    fin = None
    if ev.get('fin'):
        try:
            fin = leer_fecha(ev['fin'])[0]
        except ValueError:
            fin = None
    if fin is None or fin <= ini:
        fin = ini + (dt.timedelta(days=1) if ev.get('todo_el_dia') else dt.timedelta(hours=2))
    return ini, fin


def evento_vencido(ev, t=None):
    """True si el evento terminó hace 3 días o más (ya no se muestra)."""
    try:
        return (t or ahora()) - limites(ev)[1] >= dt.timedelta(days=3)
    except (ValueError, TypeError):
        return False


def umbral_actual(ev, t=None):
    """El umbral más urgente que aplica ahora, o None si falta más de una semana o terminó hace 3 días o más."""
    t = t or ahora()
    ini, fin = limites(ev)
    if t >= fin:
        return 'despues' if t - fin < dt.timedelta(days=3) else None
    if t >= ini:
        return 'ahora'
    falta = ini - t
    for umbral, horas in (('3h', 3), ('1d', 24), ('2d', 48), ('7d', 168)):
        if falta <= dt.timedelta(hours=horas):
            return umbral
    return None


def marcar_umbral(ev, t=None):
    """Regla de disparo: devuelve el umbral a avisar (una sola vez) y lo anota en 'avisos' junto con
    todos los anteriores, para que un evento que aparece a 1 día no avise también '7d' y '2d'."""
    umbral = umbral_actual(ev, t)
    avisos = [x for x in (ev.get('avisos') or []) if x in UMBRALES]
    if umbral is None or umbral in avisos:
        return None
    hasta = UMBRALES.index(umbral)
    ev['avisos'] = [x for i, x in enumerate(UMBRALES) if i <= hasta or x in avisos]
    return umbral


def ciudad(zona):
    parte = (zona or ZONA_LOCAL).split('/')[-1]
    return CIUDADES.get(parte, parte.replace('_', ' '))


def fecha_legible(ev, t=None):
    """'sábado 26 de septiembre, 08:00 · Bogotá', en la zona del evento o en la de Santo Domingo."""
    t = t or ahora()
    ini = leer_fecha(ev.get('inicio'))[0]
    if not ev.get('todo_el_dia'):                  # todo el día: la fecha tal como se guardó
        ini = ini.astimezone(zona_tz(ev.get('zona')))
    txt = f'{DIAS[ini.weekday()]} {ini.day} de {MESES[ini.month - 1]}'
    if ini.year != t.year:
        txt += f' de {ini.year}'
    if ev.get('todo_el_dia'):
        return txt + ', todo el día'
    return f'{txt}, {ini:%H:%M} · {ciudad(ev.get("zona"))}'


def texto_aviso(ev, umbral, t=None):
    t = t or ahora()
    frase = FRASES[umbral]
    if umbral == '1d' and not ev.get('todo_el_dia'):   # si es más tarde hoy, no decir "mañana"
        tz = zona_tz(ev.get('zona'))
        if leer_fecha(ev['inicio'])[0].astimezone(tz).date() == t.astimezone(tz).date():
            frase = 'Hoy es «{titulo}» ({fecha}).'
    return frase.format(titulo=ev.get('titulo', ''), fecha=fecha_legible(ev, t))


def _cantidad(n, uno, varios):
    return f'{n} {uno if n == 1 else varios}'


def duracion_legible(td):
    minutos = max(0, int(td.total_seconds() // 60))
    d, h, m = minutos // 1440, minutos % 1440 // 60, minutos % 60
    if d:
        return _cantidad(d, 'día', 'días') + (' y ' + _cantidad(h, 'hora', 'horas') if h else '')
    if h:
        return _cantidad(h, 'hora', 'horas') + (' y ' + _cantidad(m, 'minuto', 'minutos') if m else '')
    return _cantidad(m, 'minuto', 'minutos')


def cuanto_falta(ev, t=None):
    """'faltan 2 días y 3 horas', 'está en curso (empezó hace 20 minutos)' o 'terminó hace 1 día'."""
    t = t or ahora()
    ini, fin = limites(ev)
    if t < ini:
        txt = duracion_legible(ini - t)
        return ('falta ' if txt.startswith('1 ') else 'faltan ') + txt
    if t < fin:
        return f'está en curso (empezó hace {duracion_legible(t - ini)})'
    return f'terminó hace {duracion_legible(t - fin)}'


def armar_evento(titulo, inicio, fin=None, lugar=None, descripcion='', fuente='hermes', todo_el_dia=False,
                 zona=None, eid=None, t=None):
    """Arma un evento con la forma que lee el hábitat. Lanza ValueError con un mensaje claro si algo no sirve."""
    t = t or ahora()
    titulo = ' '.join(str(titulo or '').split())[:140]
    if not titulo:
        raise ValueError('Escribe el nombre del evento.')
    zona = str(zona or '').strip() or None
    if zona and not zona_conocida(zona):
        raise ValueError(f'No conozco la zona horaria «{zona}». Usa un nombre como America/Bogota.')
    if inicio is None or not str(inicio).strip():
        raise ValueError('Falta la fecha del evento.')
    try:
        ini, solo_fecha = leer_fecha(inicio, zona)
    except (ValueError, OverflowError):
        raise ValueError('La fecha del evento no es válida. Usa, por ejemplo, 2026-09-26T08:00.') from None
    todo = bool(todo_el_dia or solo_fecha)
    if todo:
        ini = ini.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_d = None
    if fin is not None and str(fin).strip():
        try:
            fin_d, fin_solo = leer_fecha(fin, zona)
        except (ValueError, OverflowError):
            raise ValueError('La fecha de fin no es válida. Usa, por ejemplo, 2026-09-26T12:00.') from None
        if fin_solo:                                # una fecha sola incluye ese día completo
            fin_d += dt.timedelta(days=1)
        if fin_d <= ini:
            raise ValueError('La hora de fin debe ser posterior al inicio.')
    fuente = fuente if fuente in FUENTES else 'hermes'
    return {'id': eid or f'{FUENTES[fuente]}-{int(t.timestamp() * 1000)}', 'titulo': titulo,
            'inicio': iso(ini), 'fin': iso(fin_d) if fin_d else None, 'todo_el_dia': todo, 'zona': zona,
            'lugar': ' '.join(str(lugar or '').split())[:200] or None,
            'descripcion': str(descripcion or '').strip()[:1000], 'fuente': fuente, 'avisos': [], 'preparado': None}


def _mismo_instante(a, b):
    try:
        return leer_fecha(a)[0] == leer_fecha(b)[0]
    except (ValueError, TypeError):
        return False


def agregar_evento(data, titulo, inicio, fin=None, lugar=None, descripcion='', fuente='hermes',
                   todo_el_dia=False, zona=None, t=None):
    """Crea un evento (manual o desde Hermes), lo agrega a data['eventos'] y lo devuelve.
    Si ya hay uno con el mismo título a la misma hora, devuelve ese en vez de duplicarlo."""
    t = t or ahora()
    ev = armar_evento(titulo, inicio, fin, lugar, descripcion, fuente, todo_el_dia, zona, t=t)
    eventos = data.setdefault('eventos', [])
    for x in eventos:
        if str(x.get('titulo', '')).lower() == ev['titulo'].lower() and _mismo_instante(x.get('inicio'), ev['inicio']):
            return x
    ids, n = {x.get('id') for x in eventos}, int(t.timestamp() * 1000)
    while f'{FUENTES[ev["fuente"]]}-{n}' in ids:
        n += 1
    ev['id'] = f'{FUENTES[ev["fuente"]]}-{n}'
    eventos.append(ev)
    return ev


def recortar_eventos(eventos, t=None):
    """Deja como máximo MAX_EVENTOS (los más cercanos a hoy), ordenados por inicio."""
    t = t or ahora()

    def momento(e):
        try:
            return leer_fecha(e.get('inicio'))[0].timestamp()
        except (ValueError, TypeError, OverflowError):
            return float('inf')                       # fecha dañada: al final
    eventos = [e for e in (eventos if isinstance(eventos, list) else []) if isinstance(e, dict)]
    if len(eventos) > MAX_EVENTOS:
        ref = t.timestamp()
        eventos = sorted(eventos, key=lambda e: abs(momento(e) - ref))[:MAX_EVENTOS]
    return sorted(eventos, key=momento)


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
    ap.add_argument('--evento-nuevo', help='Agrega un evento a la Sala de Eventos: título')
    ap.add_argument('--fecha', help='Inicio del evento: 2026-09-26T08:00 (hora de Santo Domingo), con desfase, '
                                    'o 2026-09-26 para todo el día')
    ap.add_argument('--fin', help='Fin del evento (opcional, mismo formato)')
    ap.add_argument('--zona', help='Zona horaria del evento (opcional), por ejemplo America/Bogota')
    ap.add_argument('--lugar', help='Lugar del evento (opcional)')
    ap.add_argument('--descripcion', default='', help='Descripción del evento (opcional)')
    ap.add_argument('--evento', help='Id del evento al que pertenecen la tarea, la aprobación o la presentación')
    ap.add_argument('--inventario', action='store_true', help='Muestra la hoja «Inventario de proyectos»')
    ap.add_argument('--sitio', action='store_true', help='Muestra el texto de la página web de Madreperla')
    ap.add_argument('--leads', action='store_true', help='Muestra los leads registrados')
    ap.add_argument('--lead', help='Registra o actualiza un lead: nombre')
    ap.add_argument('--email', help='Correo del lead')
    ap.add_argument('--pais', help='País o ciudad del lead')
    ap.add_argument('--interes', help='Qué le interesa (zona, tipo de propiedad, proyecto)')
    ap.add_argument('--origen', help='Cómo llegó: formulario, evento, referido, redes…')
    ap.add_argument('--presupuesto', help='Rango aproximado, si lo dijo (sin datos financieros)')
    ap.add_argument('--etapa', choices=C.ETAPAS, help='Etapa del lead')
    ap.add_argument('--puntaje', type=int, choices=range(1, 6), help='Qué tan buen prospecto es, de 1 a 5')
    ap.add_argument('--nota', help='Nota corta sobre el lead')
    ap.add_argument('--cargo', help='Profesión o cargo del lead (público)')
    ap.add_argument('--fuente', help='Página https:// donde encontraste al lead (prospectos de internet)')
    ap.add_argument('--motivo', help='Por qué es compatible con Madreperla')
    ap.add_argument('--perfil', action='store_true', help='Muestra el perfil de lead compatible y las reglas de búsqueda')
    ap.add_argument('--no-contactar', help='Correo de alguien que pidió no recibir más correos')
    ap.add_argument('--con-permiso', action='store_true', help='El lead dio su permiso para recibir correos (respondió, llenó un formulario…)')
    ap.add_argument('--idioma', choices=['es', 'en'], default='es', help='Idioma del correo: es (español) o en (inglés)')
    ap.add_argument('--correo-para', help='Prepara un correo para aprobar: "Nombre <correo@dominio.com>"')
    ap.add_argument('--asunto', help='Asunto del correo')
    ap.add_argument('--subir', action='store_true', help='Además, sube estado.json a GitHub')
    ap.add_argument('--sin-subir', action='store_true', help=argparse.SUPPRESS)   # compatibilidad
    a = ap.parse_args()

    bot = handle(a.bot)
    t = ahora()
    contenido = None
    if a.inventario or a.sitio or a.leads or a.perfil:   # solo lectura: no toca estado.json
        try:
            if a.perfil:
                print(C.texto_perfil())
            if a.inventario:
                print(C.leer_inventario())
            if a.sitio:
                print(C.leer_sitio())
            if a.leads:
                print(C.texto_leads(C.leer_privado()))
        except Exception as e:
            sys.exit(f'No pude leerlo: {e}')
        if not (a.lead or a.correo_para or a.no_contactar or a.estado or a.tarea or a.mensaje or a.aprobacion or a.presentar):
            return
    correo = None
    if a.correo_para:
        try:
            nombre_dest, email_dest = C.destinatario(a.correo_para)
            if not (a.asunto or '').strip():
                raise ValueError('falta --asunto.')
            cuerpo = open(a.archivo, encoding='utf-8').read() if a.archivo else (a.contenido or a.detalle or '')
            if not cuerpo.strip():
                raise ValueError('falta el texto del correo (--archivo, --contenido o --detalle).')
        except (OSError, ValueError) as e:
            sys.exit(f'No pude preparar el correo: {e}')
        cc = C.conf_correo()
        asunto = a.asunto.strip()[:160]
        resumen = C.resumen_de(cuerpo)
        correo = {'para': email_dest, 'nombre': nombre_dest, 'asunto': asunto, 'texto': cuerpo[:20000], 'idioma': a.idioma,
                  'texto_plano': C.texto_plano(cuerpo, cc, a.idioma), 'html': C.armar_html(asunto, cuerpo, cc, resumen, a.idioma),
                  'hora': t.isoformat(), 'de': bot}
    try:                                             # se valida antes de tocar los archivos
        if a.lead and a.email:
            C.destinatario(a.email)
        if a.lead and a.fuente:
            C.fuente_valida(a.fuente)
        if a.no_contactar:
            C.destinatario(a.no_contactar)
    except ValueError as e:
        sys.exit(f'No pude registrar el lead: {e}')
    if a.presentar:
        try:
            crudo = open(a.archivo, encoding='utf-8').read() if a.archivo else (a.contenido or '')
            contenido = leer_presentacion(a.formato, crudo)
        except (OSError, ValueError) as e:
            sys.exit(f'No pude leer el contenido de la presentación: {e}')
    if a.evento_nuevo:
        if not a.fecha:
            sys.exit('Falta --fecha con el inicio del evento, por ejemplo --fecha 2026-09-26T08:00.')
        try:                                         # se valida antes de tocar estado.json
            armar_evento(a.evento_nuevo, a.fecha, a.fin, a.lugar, a.descripcion, 'hermes', zona=a.zona, t=t)
        except ValueError as e:
            sys.exit(f'No pude crear el evento: {e}')
    evento_nuevo, evento_creado, evento_desconocido = None, False, False

    try:
        with Bloqueo():
            data = leer()
            ag = agente(data, bot, t)

            if a.evento_nuevo:
                antes = len(data['eventos'])
                evento_nuevo = agregar_evento(data, a.evento_nuevo, a.fecha, a.fin, a.lugar, a.descripcion,
                                              'hermes', zona=a.zona, t=t)
                evento_creado = len(data['eventos']) > antes
                if evento_creado:
                    ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Agendó: ' + evento_nuevo['titulo']})
            evento_id = a.evento or (evento_nuevo['id'] if evento_nuevo else None)   # vínculo con el evento
            vinculo = {'evento': evento_id} if evento_id else {}
            if a.evento and not any(x.get('id') == a.evento for x in data['eventos']):
                evento_desconocido = True

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
                    agregar_mensaje(data, bot, a.mensaje, para=destino, tipo='tarea', t=t, estado='pendiente', **vinculo)
                    otro = next((x for x in data['agentes'] if x.get('id') == destino), None)
                    if otro is not None:
                        otro['cola'] = (otro.get('cola', []) + [a.mensaje])[-5:]
                else:
                    agregar_mensaje(data, bot, a.mensaje, para=handle(a.para), tipo=a.tipo, t=t)

            if a.presentar:
                agregar_presentacion(data, bot, a.presentar, a.formato, contenido, t, evento_id)
                ag['estado'], ag['sala'] = 'reunion', 'meeting'
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Presentó: ' + a.presentar})
            if a.terminar_presentacion:
                for x in data.get('presentaciones', []):
                    x['activa'] = False

            if a.lead or correo or a.no_contactar:
                priv = C.leer_privado()
                if a.no_contactar:
                    quien = C.no_contactar(priv, t, a.no_contactar).lower()
                    for aid, c in priv['correos'].items():         # sus correos pendientes se retiran solos
                        ap_p = next((x for x in data['aprobaciones'] if x.get('id') == aid and x.get('estado') == 'pendiente'), None)
                        if ap_p and (c.get('para') or '').lower() == quien:
                            ap_p.update({'estado': 'devuelta', 'comentario': 'La persona pidió no recibir más correos.',
                                         'decidido': t.isoformat()})
                            c['estado'] = 'devuelta'
                    ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Anotó a alguien en «no contactar»'})
                if a.lead:
                    lead, lead_nuevo = C.guardar_lead(priv, t, bot, a.lead, a.email, pais=a.pais, interes=a.interes,
                                                      origen=a.origen, presupuesto=a.presupuesto, nota=a.nota,
                                                      etapa=a.etapa, puntaje=a.puntaje, cargo=a.cargo,
                                                      fuente=a.fuente, motivo=a.motivo, permiso=a.con_permiso)
                    ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'),
                                                              'texto': ('Registró un lead' if lead_nuevo else 'Actualizó un lead')
                                                              + (f' ({lead["puntaje"]}/5)' if lead.get('puntaje') else '')})
                if correo:
                    if C.bloqueado(priv, correo['para']):
                        raise ValueError('esa persona pidió no recibir correos de Madreperla. No le escribas.')
                    lead_c = C.buscar_lead(priv, correo['para'])
                    if lead_c:
                        correo['lead'] = lead_c['id']
                        if lead_c.get('tipo') == 'prospecto' and not lead_c.get('permiso'):   # primer contacto en frío
                            if not C.puede_escribir(lead_c):
                                donde = lead_c.get('pais') or 'un país sin anotar'
                                raise ValueError(f'{lead_c.get("nombre", "esta persona")} está en {donde}, donde hace falta su permiso '
                                                 'antes del primer correo. Queda como prospecto: el primer contacto va por LinkedIn, '
                                                 'un evento o un referido. Si da su permiso, anótalo con --lead y --con-permiso.')
                            cc2 = C.conf_correo()
                            if not cc2['direccion'].strip():
                                raise ValueError('falta la dirección física de la oficina en bots.json › correo › direccion. '
                                                 'Los correos de primer contacto la llevan al pie.')
                            tope = C.conf_leads()['por_dia']
                            if C.correos_a_prospectos_hoy(priv, t) >= tope:
                                raise ValueError(f'ya se llegó al límite de {tope} {"correo" if tope == 1 else "correos"} a '
                                                 'prospectos por hoy (bots.json › leads › por_dia). Deja los demás para mañana.')
                            correo['prospecto'] = True                 # lleva el aviso de comunicación comercial
                            correo['texto_plano'] = C.texto_plano(correo['texto'], cc2, correo['idioma'], True)
                            correo['html'] = C.armar_html(correo['asunto'], correo['texto'], cc2,
                                                          C.resumen_de(correo['texto']), correo['idioma'], True)
                    ap_c = agregar_aprobacion(data, bot, a.aprobacion or f'Correo: {correo["asunto"]}',
                                              correo_resumen(correo), 'correo', t, evento_id,
                                              correo={'asunto': correo['asunto']})
                    priv['correos'][ap_c['id']] = correo
                    ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Preparó un correo: ' + correo['asunto']})
                data['leads_resumen'] = C.resumen_leads(priv)
                C.guardar_privado(priv)
            elif a.aprobacion:
                agregar_aprobacion(data, bot, a.aprobacion, a.detalle, a.clase, t, evento_id)
                ag.setdefault('historial', []).insert(0, {'hora': t.strftime('%H:%M'), 'texto': 'Pidió aprobación: ' + a.aprobacion})

            ag['historial'] = ag.get('historial', [])[:MAX_HISTORIAL]
            ag['ultima_actividad'] = t.isoformat()
            guardar(data, t)
    except RuntimeError as e:
        sys.exit(str(e))
    except ValueError as e:                          # nada se guardó
        sys.exit(f'No pude completarlo: {e}')

    if a.subir:
        subir(bot)
    print(f'Listo: {bot} reportado.')
    if correo:
        print(f'Correo para aprobar: «{correo["asunto"]}». María Andrea lo verá en Aprobaciones con la vista previa. '
              'No lo envíes: espera su aprobación.')
    if evento_nuevo:
        estado = 'Evento creado' if evento_creado else 'Ese evento ya existía'
        print(f'{estado}: {evento_nuevo["id"]} · «{evento_nuevo["titulo"]}» ({fecha_legible(evento_nuevo, t)}).')
        print(f'Para vincular tareas, aprobaciones o presentaciones usa: --evento {evento_nuevo["id"]}')
    if evento_desconocido:
        print(f'Aviso: no encontré el evento {a.evento} en el hábitat; igual quedó vinculado.')


if __name__ == '__main__':
    main()
