# django_moxutils

## Installation

## Setup
In `settings.py` of you django project evaluate the variable

```
DjangoAuthGroups=["gorup_name1","group_name2"]
```

where `["gorup_name1","group_name2"]` is a list of names of Django auth groups (`django.contrib.auth.models.Group`) that sould be associated to each new created customer.

When a new Customer object is created in the django admin, the corresponding django user is created, as staff member (i.e. with access to the admin) and associated to the django auth group indicated in this variable.