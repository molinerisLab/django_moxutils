#-*- coding: utf-8 -*-
# Create your views here.
import HTMLParser
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMessage

punteggiatura_da_rimuovere = [t.encode('utf-8') for t in [',', ';', '.', ':', '_', '?', '!', '$', '^', '=', '&', '%', '"', '+']]


def ucfisrt(s):
	if len(s)>1:
		return s[0].capitalize() + s[1:]
	else:
		return s.capitalize()

def normalizza_apici(s):
        return s.replace(u"’","'").replace(u"‘","'").replace(u"`","'").replace(u'”','"').replace(u'“','"')

def rimuovi_punteggiatura_simboli_e_virgolette(s):
    s=normalizza_apici(s)
    for x in punteggiatura_da_rimuovere:
        s = s.replace(x, '')
    return s

def encoded(s):
    h=HTMLParser.HTMLParser()
    s=h.unescape(s)
    return s


#def to_file(filename):
#	fh = open(filename,'w')
#	def decorator(function):
#		def wrapper(*args, **kwargs):
#			for l in function(*args, **kwargs):
#				print >> fh, l
#		return wrapper
#	return decorator
#
#@to_file("/tmp/pippo")
#def prova(a):
#	return a

def mox_send_mail(subject,text_content,to):
    return
    if to[0][-7:]!="@hsr.it":
        subject = "[email to %s dropped] %s " % (to[0],subject)
        to=("order.ctgb@hsr.it",)
    to=("ivan.molineris@ircc.it","daniela.cantarella@ircc.it")
    email = EmailMessage(
        subject,
        text_content,
        settings.EMAIL_HOST_USER,
        to,#array
        bcc=[settings.EMAIL_BCC,],
        reply_to=[settings.EMAIL_REPLY_TO]
    )
    return email.send(fail_silently=False)
