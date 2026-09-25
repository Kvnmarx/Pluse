"""
Leads y correos del Hábitat de Madreperla.

- Los leads y los correos completos (destinatario, texto, HTML) se guardan en
  puente/privado.json. Ese archivo nunca se sube a GitHub ni lo sirve la web:
  el hábitat lo pide al servidor local con la llave de la sesión.
- estado.json solo guarda lo mínimo para mostrar la aprobación (asunto y un
  resumen), sin correos ni nombres de clientes.
- Un correo aprobado se guarda como archivo .eml en habitat/correos/, listo
  para abrirlo en Mail o en Outlook y enviarlo desde tu cuenta.

Solo usa la biblioteca estándar de Python.
"""
import csv, datetime as dt, html, io, json, os, re, unicodedata, urllib.request
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr

AQUI = os.path.dirname(os.path.abspath(__file__))
PRIVADO = os.path.join(AQUI, 'privado.json')
CONFIG = os.path.join(AQUI, 'bots.json')
CARPETA_CORREOS = os.path.join(os.path.dirname(AQUI), 'correos')
MAX_LEADS = 500
MAX_CORREOS = 120
MAX_DESCARGA = 5 * 1024 * 1024
ETAPAS = ['nuevo', 'calificado', 'correo-listo', 'contactado', 'respondio', 'descartado']
SITIO_BASE = ['https://madreperlarealtors.com/', 'https://madreperlarealtors.com/en/']

# Identidad visual de Madreperla (colores seguros para correo)
MARFIL, ARENA, PETROLEO, GRAFITO, CHAMPAGNE, GRIS = '#F6F1E7', '#E9DFCC', '#0E3B43', '#2B2B2B', '#B9A27A', '#6E6A63'
SERIF = "'Cormorant Garamond', 'Playfair Display', Georgia, 'Times New Roman', serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"

CORREO_BASE = {
    'remitente': 'María Andrea López <administracion@madreperlarealtors.com>',
    'firma_nombre': 'María Andrea López',
    'firma_cargo': 'Fundadora · Madreperla Realtors',
    'telefono': '',
    'sitio': 'https://madreperlarealtors.com',
    'ciudad': 'Punta Cana, República Dominicana',
    'envio': 'borrador',        # borrador: tú lo envías desde Mail · bot: el bot lo envía tras tu aprobación
}


# ─────────────────────────── configuración y archivo privado ───────────────────────────

def config():
    try:
        with open(CONFIG, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def conf_correo(cfg=None):
    cfg = cfg if cfg is not None else config()
    c = dict(CORREO_BASE)
    c.update({k: v for k, v in (cfg.get('correo') or {}).items() if k in CORREO_BASE and isinstance(v, str)})
    if c['envio'] not in ('borrador', 'bot'):
        c['envio'] = 'borrador'
    return c


def leer_privado():
    try:
        with open(PRIVADO, encoding='utf-8') as f:
            p = json.load(f)
    except (OSError, ValueError):
        p = {}
    if not isinstance(p.get('leads'), list):
        p['leads'] = []
    if not isinstance(p.get('correos'), dict):
        p['correos'] = {}
    return p


def guardar_privado(p):
    p['leads'] = p['leads'][-MAX_LEADS:]
    if len(p['correos']) > MAX_CORREOS:
        viejos = sorted(p['correos'], key=lambda k: p['correos'][k].get('hora', ''))[:-MAX_CORREOS]
        for k in viejos:
            p['correos'].pop(k, None)
    tmp = PRIVADO + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(p, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PRIVADO)
    try:
        os.chmod(PRIVADO, 0o600)
    except OSError:
        pass


def resumen_leads(p):
    """Solo conteos: es lo único de los leads que va a estado.json."""
    leads = p['leads']
    return {'total': len(leads),
            'por_etapa': {e: sum(1 for x in leads if x.get('etapa') == e) for e in ETAPAS},
            'calientes': sum(1 for x in leads if (x.get('puntaje') or 0) >= 4 and x.get('etapa') != 'descartado')}


# ─────────────────────────── leads ───────────────────────────

CORREO_RE = re.compile(r'^[^@\s<>"]+@[^@\s<>"]+\.[A-Za-z]{2,}$')


def destinatario(valor):
    """'Ana Pérez <ana@correo.com>' o 'ana@correo.com' → (nombre, correo). Error si no es válido."""
    nombre, correo = parseaddr((valor or '').strip())
    correo = correo.strip()
    if not CORREO_RE.match(correo):
        raise ValueError(f'«{valor}» no es un correo válido.')
    return nombre.strip(), correo


def buscar_lead(p, clave):
    clave = (clave or '').strip().lower()
    return next((x for x in p['leads'] if x['id'] == clave or (x.get('correo') or '').lower() == clave), None)


def guardar_lead(p, t, de, nombre, correo=None, **datos):
    """Crea o actualiza un lead (se reconoce por su correo o, sin correo, por su nombre)."""
    if correo:
        _, correo = destinatario(correo)
    lead = buscar_lead(p, correo) if correo else next(
        (x for x in p['leads'] if not x.get('correo') and x.get('nombre', '').lower() == nombre.strip().lower()), None)
    nuevo = lead is None
    if nuevo:
        lead = {'id': f'l{int(t.timestamp() * 1000)}', 'creado': t.isoformat(), 'etapa': 'nuevo', 'por': de}
        p['leads'].append(lead)
    lead['nombre'] = nombre.strip()[:120]
    if correo:
        lead['correo'] = correo
    for k in ('pais', 'interes', 'origen', 'presupuesto', 'nota'):
        if datos.get(k):
            lead[k] = str(datos[k]).strip()[:600]
    if datos.get('etapa'):
        lead['etapa'] = datos['etapa']
    if datos.get('puntaje') is not None:
        lead['puntaje'] = max(1, min(5, int(datos['puntaje'])))
    lead['actualizado'] = t.isoformat()
    return lead, nuevo


def texto_leads(p):
    if not p['leads']:
        return 'Todavía no hay leads registrados.'
    filas = []
    for x in sorted(p['leads'], key=lambda x: (-(x.get('puntaje') or 0), x.get('actualizado', ''))):
        partes = [x['id'], x.get('nombre', ''), x.get('correo', 'sin correo'), x.get('etapa', 'nuevo')]
        if x.get('puntaje'):
            partes.append(f'puntaje {x["puntaje"]}/5')
        for k in ('pais', 'interes', 'origen'):
            if x.get(k):
                partes.append(f'{k}: {x[k]}')
        filas.append(' · '.join(partes))
    return '\n'.join(filas)


# ─────────────────────────── correo con la identidad de Madreperla ───────────────────────────

def _en_linea(t):
    """Escapa y aplica **negrita**. Los enlaces sueltos quedan como texto (nada de rastreo)."""
    t = html.escape(t, quote=False)
    return re.sub(r'\*\*(.+?)\*\*', rf'<strong style="color:{GRAFITO};font-weight:600">\1</strong>', t)


BOTON_RE = re.compile(r'^\[(?:bot[oó]n:\s*)?([^\]]{1,60})\]\((https://[^\s)]{1,300})\)$', re.I)


def bloques(texto):
    """Texto simple → bloques. Formato que entienden los bots:
       línea en blanco = nuevo párrafo · '## Título' = subtítulo · '- punto' = lista ·
       '[Texto del botón](https://…)' sola en su línea = botón · '**negrita**'."""
    out, parrafo, lista = [], [], []

    def cerrar():
        if parrafo:
            out.append(('p', ' '.join(parrafo)))
            parrafo.clear()
        if lista:
            out.append(('ul', list(lista)))
            lista.clear()
    for linea in (texto or '').replace('\r\n', '\n').split('\n'):
        s = linea.strip()
        if not s:
            cerrar()
        elif s.startswith('## ') or s.startswith('# '):
            cerrar()
            out.append(('h', s.lstrip('#').strip()))
        elif s[:2] in ('- ', '• ', '* '):
            if parrafo:
                out.append(('p', ' '.join(parrafo)))
                parrafo.clear()
            lista.append(s[2:].strip())
        elif BOTON_RE.match(s):
            cerrar()
            m = BOTON_RE.match(s)
            out.append(('boton', (m.group(1).strip(), m.group(2))))
        else:
            if lista:
                out.append(('ul', list(lista)))
                lista.clear()
            parrafo.append(s)
    cerrar()
    return out


def texto_plano(texto, c):
    lineas = []
    for tipo, v in bloques(texto):
        if tipo == 'h':
            lineas += [v.upper(), '']
        elif tipo == 'ul':
            lineas += [f'— {re.sub(r"[*]{2}", "", x)}' for x in v] + ['']
        elif tipo == 'boton':
            lineas += [f'{v[0]}: {v[1]}', '']
        else:
            lineas += [re.sub(r'\*\*', '', v), '']
    lineas += [c['firma_nombre'], c['firma_cargo']]
    lineas += [x for x in (c['telefono'], c['sitio'].replace('https://', ''), c['ciudad']) if x]
    lineas += ['', 'Si prefiere no recibir más comunicaciones nuestras, responda a este correo y lo retiraremos de la lista.']
    return '\n'.join(lineas)


def armar_html(asunto, texto, c=None, resumen=''):
    """Correo HTML de una columna (600 px), con tablas y estilos en línea para que se vea bien
    en Gmail, Outlook y Apple Mail. Sin imágenes externas ni píxeles de rastreo."""
    c = c or conf_correo()
    partes = []
    for tipo, v in bloques(texto):
        if tipo == 'h':
            partes.append(f'<h2 style="margin:28px 0 10px;font-family:{SERIF};font-size:23px;line-height:1.25;'
                          f'font-weight:500;color:{PETROLEO}">{_en_linea(v)}</h2>')
        elif tipo == 'ul':
            items = ''.join(f'<tr><td valign="top" style="width:18px;padding:0 0 8px;color:{CHAMPAGNE};font-size:15px;'
                            f'line-height:1.65">—</td><td style="padding:0 0 8px;font-family:{SANS};font-size:15px;'
                            f'line-height:1.65;color:{GRAFITO}">{_en_linea(x)}</td></tr>' for x in v)
            partes.append(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                          f'style="margin:0 0 16px">{items}</table>')
        elif tipo == 'boton':
            etiqueta, url = v
            partes.append(
                f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:26px 0 22px">'
                f'<tr><td style="background:{PETROLEO};border-radius:2px">'
                f'<a href="{html.escape(url)}" style="display:inline-block;padding:14px 30px;font-family:{SANS};'
                f'font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:{MARFIL};text-decoration:none">'
                f'{html.escape(etiqueta)}</a></td></tr></table>')
        else:
            partes.append(f'<p style="margin:0 0 16px;font-family:{SANS};font-size:15px;line-height:1.7;'
                          f'color:{GRAFITO}">{_en_linea(v)}</p>')
    contacto = ' · '.join(html.escape(x) for x in (c['telefono'], c['sitio'].replace('https://', ''), c['ciudad']) if x)
    oculto = html.escape(resumen or '')
    return f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{html.escape(asunto)}</title>
<style>@media (max-width:480px){{.pad{{padding-left:24px!important;padding-right:24px!important}}.h1{{font-size:25px!important}}.logo{{font-size:24px!important;letter-spacing:.22em!important}}}}</style></head>
<body style="margin:0;padding:0;background:{ARENA}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{oculto}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{ARENA}">
<tr><td align="center" style="padding:32px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background:{MARFIL}">
<tr><td class="pad" style="background:{PETROLEO};padding:34px 44px 30px;text-align:center">
  <div class="logo" style="font-family:{SERIF};font-size:30px;letter-spacing:.32em;color:{MARFIL};font-weight:500">MADREPERLA</div>
  <div style="margin-top:8px;font-family:{SANS};font-size:10px;letter-spacing:.5em;color:{CHAMPAGNE}">REALTORS</div>
</td></tr>
<tr><td style="height:3px;background:{CHAMPAGNE};line-height:3px;font-size:0">&nbsp;</td></tr>
<tr><td class="pad" style="padding:44px 44px 12px">
  <h1 class="h1" style="margin:0 0 26px;font-family:{SERIF};font-size:29px;line-height:1.22;font-weight:500;color:{PETROLEO}">{html.escape(asunto)}</h1>
  {''.join(partes)}
</td></tr>
<tr><td class="pad" style="padding:8px 44px 40px">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
    <td style="border-left:2px solid {CHAMPAGNE};padding:2px 0 2px 16px">
      <div style="font-family:{SERIF};font-size:20px;color:{PETROLEO}">{html.escape(c['firma_nombre'])}</div>
      <div style="margin-top:4px;font-family:{SANS};font-size:12px;letter-spacing:.06em;color:{GRIS}">{html.escape(c['firma_cargo'])}</div>
    </td></tr></table>
</td></tr>
<tr><td class="pad" style="background:{PETROLEO};padding:22px 44px;text-align:center;font-family:{SANS};font-size:11px;line-height:1.7;color:#C9D3D1">
  {contacto}<br>
  <span style="color:#9FB1AE">Si prefiere no recibir más comunicaciones nuestras, responda a este correo y lo retiraremos de la lista.</span>
</td></tr>
</table>
</td></tr></table>
</body></html>'''


def resumen_de(texto, largo=140):
    plano = re.sub(r'\s+', ' ', re.sub(r'[#*\[\]]|\(https://[^)]*\)', '', texto or '')).strip()
    return plano[:largo - 1] + '…' if len(plano) > largo else plano


def armar_eml(correo, c=None):
    """Archivo .eml con versión de texto y HTML. X-Unsent hace que Outlook lo abra como borrador;
    en Apple Mail se abre y se envía con Mensaje › Volver a enviar."""
    c = c or conf_correo()
    m = EmailMessage()
    m['Subject'] = correo['asunto']
    m['To'] = formataddr((correo.get('nombre') or '', correo['para']))
    remitente = parseaddr(c['remitente'])
    if remitente[1]:
        m['From'] = formataddr(remitente)
    m['Date'] = formatdate(localtime=True)
    m['Message-ID'] = make_msgid(domain='madreperlarealtors.com')
    m['X-Unsent'] = '1'
    m.set_content(correo['texto_plano'])
    m.add_alternative(correo['html'], subtype='html')
    return m.as_bytes()


def guardar_eml(aid, correo, t, c=None):
    os.makedirs(CARPETA_CORREOS, exist_ok=True)
    plano = unicodedata.normalize('NFKD', correo['asunto'].lower()).encode('ascii', 'ignore').decode()
    base = re.sub(r'[^a-z0-9]+', '-', plano).strip('-')[:50] or 'correo'
    ruta = os.path.join(CARPETA_CORREOS, f'{t.strftime("%Y-%m-%d_%H%M")}_{base}_{aid[-6:]}.eml')
    with open(ruta, 'wb') as f:
        f.write(armar_eml(correo, c))
    return ruta


# ─────────────────────────── fuentes: inventario y sitio web ───────────────────────────

def _descargar(url, espera=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'Habitat-Madreperla/1.0'})
    with urllib.request.urlopen(req, timeout=espera) as r:
        datos = r.read(MAX_DESCARGA + 1)
        if len(datos) > MAX_DESCARGA:
            raise ValueError('el archivo es demasiado grande')
        tipo = r.headers.get_content_charset() or 'utf-8'
    return datos.decode(tipo, errors='replace')


def url_csv(url):
    """Acepta el enlace normal de Google Sheets y lo convierte en su descarga CSV."""
    m = re.search(r'docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)', url or '')
    if m and 'output=csv' not in url and 'format=csv' not in url and '/d/e/' not in url:
        gid = re.search(r'[#&?]gid=(\d+)', url)
        return f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv' + (f'&gid={gid.group(1)}' if gid else '')
    return url


def leer_inventario(cfg=None):
    cfg = cfg if cfg is not None else config()
    url = (cfg.get('inventario') or '').strip()
    if not url.startswith('https://'):
        raise ValueError('falta "inventario" en puente/bots.json (el enlace de la hoja «Inventario de proyectos»).')
    crudo = _descargar(url_csv(url))
    if crudo.lstrip().lower().startswith(('<!doctype', '<html')):
        raise ValueError('Google devolvió una página, no la hoja. Comparte la hoja como «Cualquier persona con el '
                         'enlace puede ver» o publícala en la web como CSV.')
    filas = [f for f in csv.reader(io.StringIO(crudo)) if any(x.strip() for x in f)]
    if not filas:
        raise ValueError('la hoja está vacía.')
    enc, datos = [h.strip() or f'Columna {i + 1}' for i, h in enumerate(filas[0])], filas[1:]
    lineas = [f'Inventario de proyectos · {len(datos)} filas · leído {dt.datetime.now():%Y-%m-%d %H:%M}']
    for f in datos[:300]:
        lineas.append(' | '.join(f'{enc[i] if i < len(enc) else f"Columna {i + 1}"}: {v.strip()}'
                                 for i, v in enumerate(f) if v.strip()))
    return '\n'.join(lineas)


def texto_de_pagina(crudo):
    crudo = re.sub(r'(?is)<(script|style|noscript|svg|head|nav)\b.*?</\1>', ' ', crudo)
    crudo = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h[1-6]|section|article|tr)>', '\n', crudo)
    texto = html.unescape(re.sub(r'<[^>]+>', ' ', crudo))
    lineas = [re.sub(r'[ \t\xa0]+', ' ', x).strip() for x in texto.split('\n')]
    vistas, out = set(), []
    for x in lineas:                                        # quita menús y pies repetidos
        if len(x) > 2 and x not in vistas:
            vistas.add(x)
            out.append(x)
    return '\n'.join(out)


def leer_sitio(cfg=None, maximo=7000):
    cfg = cfg if cfg is not None else config()
    urls = cfg.get('sitio') or SITIO_BASE
    partes = []
    for url in urls[:8]:
        try:
            partes.append(f'### {url}\n' + texto_de_pagina(_descargar(url))[:maximo])
        except Exception as e:
            partes.append(f'### {url}\n(No pude leer esta página: {e})')
    return '\n\n'.join(partes)
