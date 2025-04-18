from django.contrib import admin
from .models import Sklad, AuditLog, Dodavatele, Zarizeni, Varianty, Poptavky, PoptavkaVarianty
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
admin.site.register(AuditLog)
admin.site.register(Dodavatele)
admin.site.register(Zarizeni)
admin.site.register(Varianty)
admin.site.register(Poptavky)
admin.site.register(PoptavkaVarianty)

@admin.register(Sklad)
class SkladAdmin(SimpleHistoryAdmin):
    list_display = ("evidencni_cislo", "nazev_dilu", "poznamka")
    search_fields = ("evidencni_cislo", "nazev_dilu__startswith")
    list_filter = ("kriticky_dil", "ucetnictvi", "datum_nakupu")

    history_list_display = ["evidencni_cislo", "nazev_dilu", "dodavatel", "mnozstvi", "min_mnozstvi_ks"]
    history_search_fields = ["nazev_dilu", "dodavatel"]