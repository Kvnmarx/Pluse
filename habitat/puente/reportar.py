#!/usr/bin/env python3
"""
Puente Hermes → Hábitat de Madreperla.

Cada bot de Hermes ejecuta este script cuando empieza, avanza o termina una
tarea, o cuando quiere decir algo en el chat del equipo. El script actualiza
estado.json (el archivo que lee el hábitat) y, si la carpeta es un repositorio
de git, lo sube a GitHub para que la página lo vea.

Ejemplos:
  python3 reportar.py --bot @mark --estado trabajando --tarea "Midiendo leads de la semana" --avance 40
  python3 reportar.py --bot @sylvia --mensaje "Prioridades de hoy: leads y calendario" --para todos
  python3 reportar.py --bot @sylvia --tarea-para @contenido-madreperla --mensaje "Calendario de octubre"
  python3 reportar.py --bot @mark --tokens-entrada 1200 --tokens-salida 300
  python3 reportar.py --bot @marcelo --estado inactivo --sin-subir

No escribas datos sensibles de clientes (cédulas, cuentas, montos): el archivo
puede quedar público junto con la página.
"""
import argparse, datetime as dt, json, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(os.path.dirname(AQUI), 'estado.json')
BLOQUEO = ESTADO + '.lock'
ESTADOS = ['trabajando', 'pensando', 'reunion', 'inactivo', 'error']
SALAS = ['code', 'design', 'analitica', 'libreria', 'archivo', 'ventas', 'meeting']
MAX_MENSAJES = 200
MAX_HISTORIAL = 8


def ahora():
    return dt.datetime.now().astimezone()


class Bloqueo:
    """Evita que dos bots escriban el archivo al mismo tiempo."""
    def __enter__(self):
        for _ in range(100):
            try:
                self.fd = os.open(BLOQUEO, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - os.path.getmtime(BLOQUEO) > 30:   # bloqueo abandonado
                    os.remove(BLOQUEO)
                time.sleep(0.2)
        sys.exit('No pude tomar el archivo: otro bot lo está usando. Intenta de nuevo.')

    def __exit__(self, *a):
        os.close(self.fd)
        os.remove(BLOQUEO)


def leer():
    if not os.path.exists(ESTADO):
        return {'actualizado': None, 'agentes': [], 'mensajes': []}
    with open(ESTADO, encoding='utf-8') as f:
        return json.load(f)


def guardar(data):
    tmp = ESTADO + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ESTADO)


def git(*args):
    return subprocess.run(['git', '-C', os.path.dirname(ESTADO), *args], capture_output=True, text=True)


def subir(bot):
    if git('rev-parse', '--is-inside-work-tree').returncode != 0:
        print('Aviso: la carpeta no es un repositorio de git; estado.json se guardó solo en esta computadora.')
        return
    git('add', 'estado.json')
    if git('diff', '--cached', '--quiet').returncode == 0:
        return
    git('commit', '-m', f'Reporte de {bot}')
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
    ap.add_argument('--sin-subir', action='store_true', help='Guarda sin subir a GitHub')
    a = ap.parse_args()

    bot = a.bot if a.bot.startswith('@') else '@' + a.bot
    t = ahora()
    hoy, hora = t.strftime('%Y-%m-%d'), t.strftime('%Y-%m-%dT%H')

    with Bloqueo():
        data = leer()
        ag = next((x for x in data['agentes'] if x.get('id') == bot), None)
        if ag is None:
            ag = {'id': bot, 'estado': 'inactivo', 'tarea': ''}
            data['agentes'].append(ag)

        # contadores del día: se reinician solos al cambiar de fecha
        if ag.get('_dia') != hoy:
            ag.update({'_dia': hoy, 'completadas_hoy': 0, 'activo_desde': t.isoformat(),
                       'tokens': {'entrada': 0, 'salida': 0, 'por_hora': []}, '_horas': {}})

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
            ag['tokens']['limite_diario'] = a.limite_diario

        if a.tokens_entrada or a.tokens_salida:
            tk = ag['tokens']
            tk['entrada'] = tk.get('entrada', 0) + a.tokens_entrada
            tk['salida'] = tk.get('salida', 0) + a.tokens_salida
            horas = ag.setdefault('_horas', {})
            horas[hora] = horas.get(hora, 0) + a.tokens_entrada + a.tokens_salida
            ultimas = [(t - dt.timedelta(hours=h)).strftime('%Y-%m-%dT%H') for h in range(11, -1, -1)]
            tk['por_hora'] = [horas.get(h, 0) for h in ultimas]
            ag['_horas'] = {h: horas[h] for h in ultimas if h in horas}

        ag['historial'] = ag.get('historial', [])[:MAX_HISTORIAL]
        ag['ultima_actividad'] = t.isoformat()

        if a.mensaje:
            msgs = data.setdefault('mensajes', [])
            nuevo = {'id': f'{int(t.timestamp()*1000)}-{bot}', 'de': bot, 'texto': a.mensaje, 'hora': t.isoformat()}
            if a.tarea_para:
                destino = a.tarea_para if a.tarea_para.startswith('@') else '@' + a.tarea_para
                nuevo.update({'para': destino, 'tipo': 'tarea', 'estado': 'pendiente'})
                otro = next((x for x in data['agentes'] if x.get('id') == destino), None)
                if otro is not None:
                    otro['cola'] = (otro.get('cola', []) + [a.mensaje])[-5:]
            else:
                para = a.para if a.para in ('todos', 'tu') or a.para.startswith('@') else '@' + a.para
                nuevo.update({'para': para, 'tipo': a.tipo})
            msgs.append(nuevo)
            data['mensajes'] = msgs[-MAX_MENSAJES:]

        data['actualizado'] = t.isoformat()
        guardar(data)

    if not a.sin_subir:
        subir(bot)
    print(f'Listo: {bot} reportado.')


if __name__ == '__main__':
    main()
