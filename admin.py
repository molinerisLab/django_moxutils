# -*- coding: utf-8 -*-

from sys import stdout
from django.contrib import admin
from django import forms
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.auth.models import User
#from django.shortcuts import render_to_response
#from django.template import RequestContext
import re
from moxutils.models import WithDateAndOwner, Customer, CustomerGroup
#Inclusioni per csv export
from django.http import HttpResponse
from django.db.models.query import QuerySet
from django.db.models.fields.files import FieldFile
from django.conf import settings
import csv
#########################

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

def check_permission(request, obj):
    if request.user.is_superuser:
        return True
    elif obj.owner == request.user:
        return True
    elif request.user.groups.filter(name=settings.MOXUTILS_SUPERGROUP).exists():
        return True
    elif request.user.related_customer.group == obj.owner.related_customer.group:
        return True
    elif hasattr(obj, 'get_allowed_users') and request.user in obj.get_allowed_users():
        return True
    else:
        return False

def save_with_date_and_owner(self, request, obj, form, change):
    if not change:
        obj.owner = request.user
        obj.save()
    elif check_permission(request, obj):
        obj.save()
    else:
        raise Exception(f"__MolError__ Non sei il proprietario di questo oggetto, quindi non puoi modificarlo. Il proprietario è {obj.owner.username}")
        #Non ri puo` fare, provare con un redirect return render_to_response('athome/error.html', { 'error': "Non sei il proprietario o il revisore di questo oggetto, quindi non puoi modificarlo" }, context_instance=RequestContext(request))

class WithDateAndOwnerAdmin_show(admin.ModelAdmin):
    exclude=("owner","created","updated")
    def save_model(self, request, obj, form, change):
        save_with_date_and_owner(self, request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if hasattr(instance, 'owner_id'):
                if not instance.owner_id:
                    instance.owner_id = request.user.pk
            instance.save()
        formset.save_m2m()

    def delete_model(self, request, obj):
        if check_permission(request, obj):
            obj.delete()
        else:
           raise Exception(f"__MolError__ Non sei il proprietario di questo oggetto, quindi non puoi eliminarlo. Il proprietario è {obj.owner}")


class WithDateAndOwnerAdmin(WithDateAndOwnerAdmin_show):
    exclude=("owner","created","updated")
    #se non sei superutente vedi solo le cose tue
    def get_queryset(self, request):
        if request.user.is_superuser or request.user.groups.filter(name=settings.MOXUTILS_SUPERGROUP).exists():
            return super(WithDateAndOwnerAdmin,self).get_queryset(request)
        else: 
            if hasattr(request.user, 'related_customer'):
                return super(WithDateAndOwnerAdmin,self).get_queryset(request).filter(
                    owner__in = User.objects.filter(
                        related_customer__in = Customer.objects.filter(
                            group = request.user.related_customer.group
                        )
                    )
                )
            else:
                return super(WithDateAndOwnerAdmin,self).get_queryset(request).filter(owner=request.user)

    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if not (request.user.is_superuser or request.user.groups.filter(name=settings.MOXUTILS_SUPERGROUP).exists()):
            if (request != None and db_field.name != None and db_field.related_model != None and hasattr(db_field.related_model, 'owner') and hasattr(request.user, 'related_customer')):
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    owner__in = User.objects.filter(
                        related_customer__in = Customer.objects.filter(
                            group = request.user.related_customer.group
                        )
                    )
                )
        return super(WithDateAndOwnerAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


            

class WithDateAndOwnerAdminStackedInline(admin.StackedInline):
    exclude = ("owner",)
    def save_model(self, request, obj, form, change):#credo che questo metodo non venga mai chiamato
        save_with_date_and_owner(self, request, obj, form, change)

class WithDateAndOwnerAdminTabularInline(admin.TabularInline):
    exclude = ("owner",)
    def save_model(self, request, obj, form, change):#credo che questo metodo non venga mai chiamato
        return save_with_date_and_owner(self, request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if not (request.user.is_superuser or request.user.groups.filter(name=settings.MOXUTILS_SUPERGROUP).exists()):
            if (request != None and db_field.name != None and db_field.related_model != None and hasattr(db_field.related_model, 'owner')):
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    owner__in = User.objects.filter(
                        related_customer__in = Customer.objects.filter(
                            group = request.user.related_customer.group
                        )
                    )
                )
        return super(WithDateAndOwnerAdminTabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class WithDateAndOwnerAdminGenericTabularInline(GenericTabularInline):
    exclude = ("owner",)
    def save_model(self, request, obj, form, change):#credo che questo metodo non venga mai chiamato
        return save_with_date_and_owner(self, request, obj, form, change)

class ShowOnlyAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            obj.save()
        else:
            raise Exception('__MolError__ Permesso negato')


#################################################
#
#     """ Generic csv export admin action.
#     Based on http://djangosnippets.org/snippets/2712/
#     """
#
# Example usage
#
#from django.contrib import admin
#
#
#class ExampleModelAdmin(admin.ModelAdmin):
#    raw_id_fields = ('field1',)
#    list_display = ('field1', 'field2', 'field3',)
#    actions = [
#        export_csv_action("Export Sepecial Report",
#            fields=[
#                ('field1', 'label1'),
#                ('foreignkey1__name', 'label2'),
#                ('manytomany__all', 'label3'),
#            ],
#            header=True,
#            manyToManySep=';'
#        ),
#    ]
#
#admin.site.register(ExampleMode, ExampleModelAdmin)



def export_csv_action(description="Export as CSV", fields=None, exclude=None, header=True,
                      manyToManySep=';'):
    """ This function returns an export csv action. """
    def export_as_csv(modeladmin, request, queryset):
        """ Generic csv export admin action.
        Based on http://djangosnippets.org/snippets/2712/
        """
        def prep_field(request, obj, field, manyToManySep=';'):
            """ Returns the field as a unicode string. If the field is a callable, it
            attempts to call it first, without arguments.
            """
            if '__' in field:
                bits = field.split('__')
                field = bits.pop()

                for bit in bits:
                    obj = getattr(obj, bit, None)

                    if obj is None:
                        return ""

            attr = getattr(obj, field)

            if isinstance(attr, (FieldFile,) ):
                attr = request.build_absolute_uri(attr.url)

            output = attr() if callable(attr) else attr

            if isinstance(output, (list, tuple, QuerySet)):
                output = manyToManySep.join([str(item) for item in output])
            return str(output).replace("\n","\\n").replace("\t","\\t").replace("\r","\\r") if output else output
        opts = modeladmin.model._meta
        field_names = [field.name for field in opts.fields]
        labels = []

        if exclude:
            field_names = [f for f in field_names if f not in exclude]

        elif fields:
            field_names = [field for field, _ in fields]
            labels = [label for _, label in fields]

        if request is not None:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s.csv' % (
                    str(opts).replace('.', '_')
                )
        else:
            response=stdout

        writer = csv.writer(response, delimiter='\t')

        if header:
            writer.writerow(labels if labels else field_names)

        for obj in queryset.iterator():
            writer.writerow([prep_field(request, obj, field, manyToManySep) for field in field_names])
        return response
    export_as_csv.short_description = description
    export_as_csv.acts_on_all = True
    return export_as_csv

@admin.register(Customer)
class CustomerAdmin(WithDateAndOwnerAdmin):
    list_display = ('user', 'group' )


@admin.register(CustomerGroup)
class CustomerGroupAdmin(WithDateAndOwnerAdmin):
    list_display = ('name', 'code' )