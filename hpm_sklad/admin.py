from django.contrib import admin

# Register your models here.
from .models import Sklad, AuditLog

# Register your models here.
admin.site.register(Sklad)
admin.site.register(AuditLog)
