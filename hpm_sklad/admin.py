from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Sklad, AuditLog, Dodavatele, Zarizeni, Varianty, Poptavky, PoptavkaVarianty
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
#admin.site.register(Poptavky)
#admin.site.register(PoptavkaVarianty)

@admin.register(Sklad)
class SkladAdmin(SimpleHistoryAdmin):
    list_display = ("evidencni_cislo", "interne_cislo", "nazev_dilu", "pod_minimem_display", "poznamka")
    search_fields = ("evidencni_cislo", "nazev_dilu")
    list_filter = ("kriticky_dil", "ucetnictvi", "datum_nakupu")

    history_list_display = ["evidencni_cislo", "nazev_dilu", "dodavatel", "mnozstvi", "min_mnozstvi_ks"]
    history_search_fields = ["nazev_dilu", "dodavatel"]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "evidencni_cislo_link", "nazev_dilu", "zmena_mnozstvi", "jednotky", "datum_nakupu", "datum_vydeje", "typ_operace")
    search_fields = ("evidencni_cislo__pk", "nazev_dilu")
    list_filter = ("ucetnictvi", "datum_nakupu", "datum_vydeje")    

    def evidencni_cislo_link(self, obj):
        evidencni_cislo = obj.evidencni_cislo.pk
        url= reverse('admin:hpm_sklad_sklad_change', args=[evidencni_cislo])
        return format_html('<a href={}>{}</a>', url, evidencni_cislo)
    evidencni_cislo_link.short_description = "ev. číslo"

    def get_fields(self, request, obj=None):
        fields = [
            'ucetnictvi', 'evidencni_cislo', 'interne_cislo', 'objednano', 'nazev_dilu',
            'zmena_mnozstvi', 'mnozstvi', 'jednotky', 'typ_operace', 'pouzite_zarizeni',
            'umisteni', 'dodavatel', 'datum_vydeje', 'datum_nakupu', 'cislo_objednavky',
            'jednotkova_cena_eur', 'celkova_cena_eur', 'typ_udrzby', 'poznamka',
        ]
        if obj and obj.typ_operace == 'PŘÍJEM':
            fields = [f for f in fields if f not in ('typ_udrzby', 'pouzite_zarizeni')]
        return fields


@admin.register(Dodavatele)
class DodavateleAdmin(admin.ModelAdmin):
    list_display = ("id", "dodavatel", "jazyk")
    search_fields = ("dodavatel", )
    list_filter = ("jazyk", )

@admin.register(Zarizeni)
class ZarizeniAdmin(admin.ModelAdmin):
    list_display = ("id", "kod_zarizeni", "nazev_zarizeni", "umisteni", "typ_zarizeni")
    search_fields = ("nazev_zarizeni", )
    list_filter = ("umisteni", "typ_zarizeni")    

@admin.register(Varianty)
class VariantyAdmin(admin.ModelAdmin):
    list_display = ("id", "sklad_link", "dodavatel_link", "nazev_varianty", "cislo_varianty")
    search_fields = ("nazev_varianty", "dodavatel__dodavatel", "sklad__pk", "sklad__nazev_dilu")

    def sklad_link(self, obj):
        evidencni_cislo = obj.sklad.pk
        url= reverse('admin:hpm_sklad_sklad_change', args=[evidencni_cislo])
        return format_html('<a href={}>{}</a>', url, evidencni_cislo)
    sklad_link.short_description = "ev. číslo"

    def dodavatel_link(self, obj):
        pk_dodavatele = obj.dodavatel.pk
        nazev_dodavatele = obj.dodavatel.dodavatel
        url= reverse('admin:hpm_sklad_dodavatele_change', args=[pk_dodavatele])
        return format_html('<a href={}>{}</a>', url, nazev_dodavatele)
    dodavatel_link.short_description = "dodavatel"