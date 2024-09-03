from django.db import models
from django.urls import reverse

class WithDateAndOwner(models.Model):
    created         = models.DateTimeField(auto_now_add=True)
    updated         = models.DateTimeField(auto_now=True)
    owner           = models.ForeignKey('auth.User', related_name="%(app_label)s_%(class)s_related", on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.id,))
