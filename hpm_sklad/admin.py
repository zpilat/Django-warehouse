from django.contrib import admin

# Register your models here.
from .models import Sklad, AuditLog, Dodavatele, Zarizeni

# Register your models here.
admin.site.register(AuditLog)
admin.site.register(Dodavatele)
admin.site.register(Zarizeni)

@admin.register(Sklad)
class SkladAdmin(admin.ModelAdmin):
    list_display = ("evidencni_cislo", "nazev_dilu", "poznamka")
    search_fields = ("evidencni_cislo", "nazev_dilu__startswith")
    list_filter = ("kriticky_dil", "ucetnictvi", "datum_nakupu")
