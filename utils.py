# -*- coding: utf-8 -*-
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from collections import defaultdict
from django.conf import settings
import subprocess

try:
    from uwsgidecorators import spool
except ImportError: #per gestire chiamate da shell
    def spool(f):
        f.spool=f
        return f

# def invia_mail(oggetto, to, testo_semplice, html_content="", From=settings.DEFAULT_FROM_EMAIL, ReplyTo=settings.DEFAULT_REPLY_TO_EMAIL):
#     if isinstance(to,str) or isinstance(to,unicode):
#         to=[to,]
#     email = EmailMultiAlternatives(subject=oggetto, body=testo_semplice, to=to)
#     if html_content:
#         email.attach_alternative(html_content, "text/html")
#     email.extra_headers = {'From': From}
#     if ReplyTo is not None:
#         email.extra_headers['Reply-To']=ReplyTo
#     email.send()

def ternario(a,b,c):
    if a:
        return b
    else:
        return c

def delayed_command(cmd, delay_minutes=0):
    if settings.DEBUG:
            directory = settings.ROOT_DEV
    else:
            directory = settings.ROOT_PROD
    cmd = "bash -c 'cd %s; source ../../venv/bin/activate; %s'" % (directory, cmd)
    sched_cmd = ['at', 'now + %d minutes' % delay_minutes]
    p = subprocess.Popen(sched_cmd, stdin=subprocess.PIPE)
    p.communicate(cmd)
    if p.returncode != 0:
        raise Exception("errore nell'invio della mail")

@spool
def esegui_cmd_asincrono(env):
    sched_cmd = ['bash', '-c', '%s' % env['cmd']]
    p = subprocess.Popen(sched_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = p.communicate()
    if p.returncode!=0:
        destinatari = [ i[1] for i in settings.ADMINS]
        if env['destinatario_segnalazioni']:
            destinatari.append(env['destinatario_segnalazioni'])
        mail = "COMANDO:\n%s\n\n---------------------------\nOUTPUT:\n%s\n\n---------------------------\nERROR:\n%s" % (sched_cmd,out,err)
        invia_mail("Errore in esegui_cmd_asincrono", destinatari, mail)
    elif env['destinatario_segnalazioni']:
        destinatari = [env['destinatario_segnalazioni'],]
        mail = env['label']
        invia_mail("Processo eseguito correttamente", destinatari, mail)


def delayed_command_uwsgi_spooler(cmd, delay_minutes=0, user=None, label=None):
    if delay_minutes != 0:
        raise NotImplementedError("delay_minutes != 0 non supportato")
    if settings.DEBUG:
            directory = settings.ROOT_DEV
    else:
            directory = settings.ROOT_PROD
    cmd = "bash -c 'cd %s; source ../../venv/bin/activate; %s'" % (directory, cmd)
    user_email=""
    if user and user.is_staff:
        user_email = user.email
    env = { "cmd": cmd,
            "destinatario_segnalazioni": user_email,
            "label": label,
    }
    esegui_cmd_asincrono.spool(env)

def stout_command(cmd):
    if settings.DEBUG:
        directory = settings.ROOT_DEV
    else:
        directory = settings.ROOT_PROD
    cmd = 'cd %s; source ../../venv/bin/activate; %s'  % (directory, cmd)
    sched_cmd = ['bash', '-c', '%s' % cmd]
    p = subprocess.Popen(sched_cmd, stdout=subprocess.PIPE)
    out = p.communicate()[0]
    return out
#   while True:
#       line = p.stdout.read()
#       if not line:
#           break
#       yield line

def generate_random_slug(length=64):
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))