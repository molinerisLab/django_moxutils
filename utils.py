# -*- coding: utf-8 -*-
from eugenio.models import Versione, Domanda, Answer
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from pyquery import PyQuery as pq
from collections import defaultdict
import HTMLParser
from django.conf import settings
import subprocess
try:
    from uwsgidecorators import spool
except ImportError: #per gestire chiamate da shell
    def spool(f):
        f.spool=f
        return f

def invia_mail(oggetto, to, testo_semplice, html_content="", From=settings.DEFAULT_FROM_EMAIL, ReplyTo=settings.DEFAULT_REPLY_TO_EMAIL):
    if isinstance(to,str) or isinstance(to,unicode):
        to=[to,]
    email = EmailMultiAlternatives(subject=oggetto, body=testo_semplice, to=to)
    if html_content:
        email.attach_alternative(html_content, "text/html")
    email.extra_headers = {'From': From}
    if ReplyTo is not None:
        email.extra_headers['Reply-To']=ReplyTo
    email.send()

def sost2(retval, v=None, user_id=None):
    meno_correct_con = {}
    open_question = []
    if v:
        try:
            ver = Versione.objects.get(pk=v)
        except Versione.DoesNotExist:
            ver = None

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None

        meno_hidden_con = []
        meno_correct_con = defaultdict(lambda: ["", False])

        if user and ver:
            domande = Domanda.objects.filter(versione=ver)
            for d in domande:
                answer = Answer.objects.filter(question=d, user=user)
                if answer:
                    if d.contesto_a_scomparsa or d.contesto_a_scomparsa_aiuto_2 or d.contesto_a_scomparsa_aiuto_3:
                        primo_aiuto = False
                        secondo_aiuto = False
                        for a in answer:
                            if a.correct() == 1:
                                meno_hidden_con.extend([e for e in d.contesto.split(" ") if e])
                            else:
                                if not primo_aiuto:
                                    primo_aiuto = True
                                    meno_hidden_con.extend([e for e in d.contesto_aiuto_2.split(" ") if e])
                                elif not secondo_aiuto:
                                    secondo_aiuto = True
                                    meno_hidden_con.extend([e for e in d.contesto_aiuto_3.split(" ")if e])
                                else:
                                    pass
                    if d.risposta_nel_testo:
                        answer = answer.latest('created')
                        if answer.correct() == 1: # and answer.answer != "__SKIPPED__":
                            for e in d.contesto.split(" "):
                                if e:
                                    if answer.answer == "__SKIPPED__":
                                        meno_correct_con[e][1] = True
                                        meno_correct_con[e][0] = d.risposta
                                    else:
                                        meno_correct_con[e][0] = answer.answer_repr(indexing=retval)#TODO retval e` l'indexing -> rinominare
                    elif d.domanda_tipo == "A":
                        answer = answer.latest('created')
                        if answer.answer != "__SKIPPED__":
                            open_question.append(answer.answer)


            meno_hidden_con = set([int(e) for e in meno_hidden_con if e.count(":")==0])

        if ver:
            dc = list(ver.domanda_set.filter(contesto__isnull=False, contesto_a_scomparsa=True).exclude(contesto__exact='').values_list('contesto', flat=True))
            dc.extend(list(ver.domanda_set.filter(contesto_aiuto_2__isnull=False, contesto_a_scomparsa_aiuto_2=True).exclude(contesto_aiuto_2__exact='').values_list('contesto_aiuto_2', flat=True)))
            dc.extend(list(ver.domanda_set.filter(contesto_aiuto_3__isnull=False, contesto_a_scomparsa_aiuto_3=True).exclude(contesto_aiuto_3__exact='').values_list('contesto_aiuto_3', flat=True)))
            hidden_con = set([int(item) for sublist in [e.split(" ") for e in dc] for item in sublist if item.count(":")==0])
            if meno_hidden_con:
                hidden_con = [e for e in hidden_con if e not in meno_hidden_con]
        else:
            hidden_con = []
    else:
        hidden_con = []
    terminante = ['.', ',', '?', '!', ';', ':', '}', ']', ')', '”', '’', '\'', '...']
    concatenante = ['-', '\'', '_', '+', '=', '\\', '/', '|', '‛', '“', '`', '‘', '’', '"', '{', '[', '(']
    stilizzante = ['</em>', '</strong>']
    h= HTMLParser.HTMLParser()
    classe = "vers_ind_elem"
    classe_nascosto = "hidden_context"
    string = ""
    for key,value in retval.iteritems():
        if value[1] != 'tag_non_da_gestire':
            c = classe
            if value[2] in hidden_con:
                c = (" ").join([c, classe_nascosto])
            if value[1] != 'parola':
                c = (" ").join([c, value[1]])

            if value[1] == 'parola' or value[1] == 'img' or value[1] == 'iframe':
                if (value[0] in terminante or h.unescape(value[0]) in terminante):
                    if retval[key-1][0] in stilizzante:
                        string = string[:string.rfind(" ")] + string[string.rfind(" ")+1:]
                    else:
                        string = string[:-1]
                    string += '<span id="%d" class="%s">%s</span> '  % (value[2], c, value[0])
                elif value[0][-1] in concatenante or h.unescape(value[0][value[0].find("&"):]) in concatenante:
                    if len(value[0]) == 1:
                        string += '<span id="%d" class="%s">%s</span> '  % (value[2], c, value[0])
                    else:
                        string += '<span id="%d" class="%s">%s</span>'  % (value[2], c, value[0])
                else:
                    string += '<span id="%d" class="%s">%s</span> '  % (value[2], c, value[0])
            else:
                classed = value[0].replace(value[1], c)
                jQ = pq(classed)
                jQ('span').attr('id',str(value[2])).removeAttr("contenteditable")
                if value[1] == 'rispostaintesto_contenitore':
                    if str(value[2]) in meno_correct_con:
                        if meno_correct_con[str(value[2])][1]:
                            jQ('span').addClass('red')
                        else:
                            jQ('span').addClass('green')
                        jQ.text(h.unescape(meno_correct_con[str(value[2])][0]))
                    else:
                        jQ.text("." * len(jQ.text()))
                if value[1] == 'erroreintesto_contenitore' and str(value[2]) in meno_correct_con:
                        if meno_correct_con[str(value[2])][1]:
                            jQ('span').addClass('red')
                        else:
                            jQ('span').addClass('green')
                        jQ.text(h.unescape(meno_correct_con[str(value[2])][0]))

                string += "%s " % str(jQ)
        else:
            string += value[0]

    if open_question:
        production = u''
        for e in open_question:
            production += e
        production = '<div id="open_question">%s</div>' % production
        return string + production
    else:
        return string


def sost(retval, v=None, user_id=None):
    if v:
        try:
            ver = Versione.objects.get(pk=v)
        except Versione.DoesNotExist:
            ver = None

        if user_id and ver:
            domande = Domanda.objects.filter(versione=ver)
            user = User.objects.get(pk=user_id)
            meno_con = []
            for d in domande:
                if d.contesto_a_scomparsa or d.contesto_a_scomparsa_aiuti:
                    answer = Answer.objects.filter(question=d, user=user)
                    primo_aiuto = False
                    secondo_aiuto = False
                    for a in answer:
                        if a.correct() == 1:
                            meno_con.extend(d.contesto.split(" "))
                        else:
                            if not primo_aiuto:
                                primo_aiuto = True
                                meno_con.extend(d.contesto_aiuto_2.split(" "))
                            elif not secondo_aiuto:
                                secondo_aiuto = True
                                meno_con.extend(d.contesto_aiuto_3.split(" "))
                            else:
                                pass
            meno_con = set([int(e) for e in meno_con if e.count(":")==0])

        if ver:
            dc = list(ver.domanda_set.filter(contesto__isnull=False, contesto_a_scomparsa=True).exclude(contesto__exact='').values_list('contesto', flat=True))
            dc.extend(list(v.domanda_set.filter(contesto_aiuto_2__isnull=False, contesto_a_scomparsa_aiuti=True).exclude(contesto_aiuto_2__exact='').values_list('contesto_aiuto_2', flat=True)))
            dc.extend(list(v.domanda_set.filter(contesto_aiuto_3__isnull=False, contesto_a_scomparsa_aiuti=True).exclude(contesto_aiuto_3__exact='').values_list('contesto_aiuto_3', flat=True)))
            con = set([int(item) for sublist in [e.split(" ") for e in dc] for item in sublist if item.count(":")==0])
            if meno_con:
                con = [e for e in con if e not in meno_con]
        else:
            con = []
    else:
        con = []

    classe = "vers_ind_elem"
    classe_nascosto = " hidden_context"
    classe_latex = " mathquill-embedded-latex"

    string = ""
    for e in retval:
        if e[0] != None:
            c = classe
            if e[0] in con:
                c += classe_nascosto
            if len(e) > 2:
                if e[2] and e[2] == "latex":
                    c += classe_latex

            string += '<span id="%d" class="%s">%s</span> '  % (e[0], c, e[1])

            #if e[0] in con:
            #    string += '<span id="%d" class="vers_ind_elem hidden_context">%s</span> '  % (e[0], e[1])
            #else:
            #    string += '<span id="%d" class="vers_ind_elem">%s</span> '  % (e[0], e[1])
        else:
            string += e[1]
    return string

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
