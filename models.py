from django.db import models
from django.urls import reverse

# Create your models here.
#from django.core.exceptions import ValidationError

#def validate_even(value):
#    if value % 2 != 0:
#        raise ValidationError(u'%s is not an even number' % value)

class WithDateAndOwner(models.Model):
    created         = models.DateTimeField(auto_now_add=True)
    updated         = models.DateTimeField(auto_now=True)
    owner           = models.ForeignKey('auth.User', related_name="%(app_label)s_%(class)s_related", on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.id,))
