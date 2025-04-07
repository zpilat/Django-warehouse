import csv
from django.http import HttpResponse, FileResponse
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, F, Case, When, BooleanField, Value
from django.db import models
from django.forms import inlineformset_factory
from django_user_agents.utils import get_user_agent

import io
import logging
import datetime

import matplotlib
matplotlib.use('Agg')  # Nastavení backendu na neinteraktivní
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from PIL import Image

from .models import Sklad, AuditLog, Dodavatele, Varianty, Poptavky, PoptavkaVarianty, Zarizeni
from .forms import (SkladCreateForm, SkladUpdateForm, SkladUpdateObjednanoForm, SkladReceiptForm,
                    SkladDispatchForm, AuditLogReceiptForm, AuditLogDispatchForm, CustomUserCreationForm,
                    VariantyCreateForm, VariantyUpdateForm, PoptavkaVariantyForm, DodavateleCreateForm,
                    DodavateleUpdateForm)

logger = logging.getLogger(__name__)

def home_view(request):
    """
    Zobrazuje úvodní stránku aplikace.
    
    Parameters:
    - request: HTTP request objekt.

    Vrací:
    - render: HTML stránku `home.html` s aktuálním přihlášeným uživatelem v kontextu.
    """
    context = {'current_user': request.user}
    logger.debug(f'Zahájena view home_view s uživatelem: {context["current_user"]}')
    return render(request, "hpm_sklad/home.html", context)


@login_required
@permission_required('hpm_sklad.change_sklad', 'hpm_sklad.add_auditlog', raise_exception=True)
def receipt_form_view(request, pk):
    """
    Zpracovává příjem položky na sklad.

    Parameters:
    - request: HTTP request objekt.
    - pk: Primární klíč položky `Sklad`, která je příjímána.

    POST:
    - Zpracuje formulář příjmu položky na sklad (`SkladReceiptForm`) a audit logu (`AuditLogReceiptForm`).
    - Aktualizuje stav skladové položky a zaznamená operaci do audit logu.
    - Přesměruje uživatele na vytvoření varianty, pokud neexistuje varianta pro daného dodavatele.

    GET:
    - Zobrazí prázdné formuláře pro příjem položky a audit log.

    Vrací:
    - render: HTML stránku `receipt_audit_log.html` s formuláři a daty.
    """    
    logger.debug(f'Zahájena view receipt_form_view pro příjem na skladovou položku pk={pk}, metoda={request.method}')

    sklad_instance = get_object_or_404(Sklad, pk=pk)
    logger.debug(f'Nalezena instance skladové položky: {sklad_instance}')

    if request.method == 'POST':
        logger.debug('Request typu POST s vyplněným formulářem pro příjem zboží')
        sklad_movement_form = SkladReceiptForm(request.POST, instance=sklad_instance)
        auditlog_receipt_form = AuditLogReceiptForm(request.POST)
        if sklad_movement_form.is_valid() and auditlog_receipt_form.is_valid():
            logger.info(f'Formuláře skladu i auditlogu jsou platné, pokračuje se s uložením dat')

            try:
                updated_sklad = sklad_movement_form.save(commit=False)
                created_auditlog = auditlog_receipt_form.save(commit=False)

                logger.debug(f"Původní množství: {sklad_instance.mnozstvi}, příjem: {created_auditlog.zmena_mnozstvi}")
                    
                created_auditlog.jednotkova_cena_eur = round(updated_sklad.jednotkova_cena_eur, 2)
                created_auditlog.celkova_cena_eur = round(created_auditlog.jednotkova_cena_eur * created_auditlog.zmena_mnozstvi, 2)
                updated_sklad.mnozstvi = sklad_instance.mnozstvi + created_auditlog.zmena_mnozstvi
                updated_sklad.celkova_cena_eur = round(sklad_instance.celkova_cena_eur + created_auditlog.celkova_cena_eur, 2)
                updated_sklad.jednotkova_cena_eur = round(updated_sklad.celkova_cena_eur / updated_sklad.mnozstvi, 2)

                logger.debug(f'Výpočty aktualizace skladu při příjmu dokončeny, množství po příjmu: {updated_sklad.mnozstvi}')

                created_auditlog.typ_operace = "PŘÍJEM"
                created_auditlog.operaci_provedl = request.user
                created_auditlog.evidencni_cislo = updated_sklad

                fields_to_copy = [
                    'ucetnictvi', 'interne_cislo', 'objednano', 'nazev_dilu', 'mnozstvi',
                    'jednotky', 'umisteni', 'dodavatel', 'datum_nakupu',
                    'cislo_objednavky', 'poznamka'                
                ]

                for field in fields_to_copy:
                    setattr(created_auditlog, field, getattr(updated_sklad, field))

                
                updated_sklad.save()            
                created_auditlog.save()
                logger.info(f'Uložení úspěšné: sklad {updated_sklad.pk}, auditlog {created_auditlog.pk}')

                # Získání dodavatele z formuláře
                dodavatel_object = Dodavatele.objects.get(dodavatel=updated_sklad.dodavatel)

                # Kontrola, zda varianta existuje
                varianty = Varianty.objects.filter(sklad=sklad_instance)
                varianta_dodavatele = [var.dodavatel for var in varianty]
            
                if not varianty or dodavatel_object not in varianta_dodavatele:
                    logger.info(f'Přesměrování na vytvoření nové varianty pro dodavatele {dodavatel_object}')
                    return redirect('create_varianty_with_dodavatel', pk=pk, dodavatel=dodavatel_object.id)

                logger.debug(f'Varianta položky s dodavatelem: {dodavatel_object} už existuje')                            
                return redirect('audit_log')
            
            except Exception as e:
                logger.exception(f'Chyba při ukládání příjmu do skladu nebo auditlogu: {e}')
                raise
        
        else:
            logger.warning("Formuláře jsou neplatné")
            logger.debug(f"Errors (sklad): {sklad_movement_form.errors}")
            logger.debug(f"Errors (auditlog): {auditlog_receipt_form.errors}")
        
    else: # GET 
        logger.debug('Zobrazuji formuláře pro příjem skladové položky pro GET požadavek')
        sklad_movement_form = SkladReceiptForm(instance=sklad_instance)
        auditlog_receipt_form = AuditLogReceiptForm()

    context = {
        'sklad_movement_form': sklad_movement_form,
        'auditlog_receipt_form': auditlog_receipt_form,
        'object': sklad_instance,
    }
    return render(request, 'hpm_sklad/receipt_audit_log.html', context)


@login_required
@permission_required('hpm_sklad.change_sklad', 'hpm_sklad.add_auditlog', raise_exception=True)
def dispatch_form_view(request, pk):
    """
    Zpracovává výdej položky ze skladu.

    Parameters:
    - request: HTTP request objekt.
    - pk: Primární klíč položky `Sklad`, která je vydávána.

    POST:
    - Zpracuje formuláře pro výdej položky na skladě (`SkladDispatchForm`) a audit logu (`AuditLogDispatchForm`).
    - Aktualizuje stav skladové položky a zaznamená operaci do audit logu.
    
    GET:
    - Zobrazí prázdné formuláře pro výdej položky a audit log.

    Vrací:
    - render: HTML stránku `dispatch_audit_log.html` s formuláři a daty.
    """
    logger.debug(f'Zahájena view dispatch_form_view pro výdej skladové položky pk={pk}, metoda={request.method}')

    sklad_instance = get_object_or_404(Sklad, pk=pk)
    logger.debug(f'Nalezena instance skladové položky: {sklad_instance}')

    if request.method == 'POST':
        logger.debug('Request typu POST s vyplněným formulářem pro výdej zboží')        
        sklad_movement_form = SkladDispatchForm(request.POST, instance=sklad_instance)
        auditlog_dispatch_form = AuditLogDispatchForm(request.POST, max_mnozstvi=sklad_instance.mnozstvi)
        
        if sklad_movement_form.is_valid() and auditlog_dispatch_form.is_valid():
            logger.info('Formuláře jsou platné, pokračuje se v ukládání dat')
            
            try:
                updated_sklad = sklad_movement_form.save(commit=False)
                created_auditlog = auditlog_dispatch_form.save(commit=False)

                logger.debug(f'Původní množství: {sklad_instance.mnozstvi}, výdej: {created_auditlog.zmena_mnozstvi}')
            
                created_auditlog.jednotkova_cena_eur = sklad_instance.jednotkova_cena_eur
                created_auditlog.zmena_mnozstvi = -created_auditlog.zmena_mnozstvi
                created_auditlog.celkova_cena_eur = created_auditlog.jednotkova_cena_eur * created_auditlog.zmena_mnozstvi          
                updated_sklad.mnozstvi = sklad_instance.mnozstvi + created_auditlog.zmena_mnozstvi
                updated_sklad.celkova_cena_eur = sklad_instance.celkova_cena_eur + created_auditlog.celkova_cena_eur

                logger.debug(f'Výpočty akualizace skladu při výdeji dokončeny, množství po výdeji: {updated_sklad.mnozstvi}')

                created_auditlog.typ_operace = "VÝDEJ"
                created_auditlog.evidencni_cislo = updated_sklad
                created_auditlog.operaci_provedl = request.user

                fields_to_copy = [
                    'ucetnictvi', 'interne_cislo', 'objednano', 'nazev_dilu', 'mnozstvi',
                    'jednotky', 'umisteni', 'dodavatel', 'cislo_objednavky', 'poznamka'                
                ]

                for field in fields_to_copy:
                    setattr(created_auditlog, field, getattr(updated_sklad, field))            

                updated_sklad.save()            
                created_auditlog.save()
                logger.info(f'Uložení úspěšné: sklad {updated_sklad.pk}, auditlog {created_auditlog.pk}')

                return redirect('audit_log')
            
            except Exception as e:
                logger.exception(f'Chyba při ukládání výdeje do skladu nebo auditlogu: {e}')
                raise
            
        else:
            logger.warning("Formuláře jsou neplatné")
            logger.debug(f"Errors (sklad): {sklad_movement_form.errors}")
            logger.debug(f"Errors (auditlog): {auditlog_dispatch_form.errors}")           
                   
    else: # GET 
        logger.debug('Zobrazuji formuláře pro GET požadavek pro výdej položky')
        sklad_movement_form = SkladDispatchForm(instance=sklad_instance)
        auditlog_dispatch_form = AuditLogDispatchForm(max_mnozstvi=sklad_instance.mnozstvi)

    context = {
        'sklad_movement_form': sklad_movement_form,
        'auditlog_dispatch_form': auditlog_dispatch_form,
        'object': sklad_instance,
    }
    return render(request, 'hpm_sklad/dispatch_audit_log.html', context)


class SkladListView(LoginRequiredMixin, ListView):
    """
    Zobrazuje seznam všech položek ve skladu.

    - Povoleno pouze přihlášeným uživatelům.
    - Stránkuje výsledky (na PC) a umožňuje export do CSV.

    Template:
    - `sklad.html` pro PC, `sklad_mobile.html` pro mobilní zařízení.

    Kontext:
    - Seznam položek skladů, možnosti filtrování a řazení.
    """
    model = Sklad
    export_csv = False
    
    def get_paginate_by(self, queryset):
        """
        Určuje, zda se má použít stránkování, nebo ne.
        Na PC bude stránkování po 20 záznamech, na mobilu se zobrazí vše.
        """
        if get_user_agent(self.request).is_pc:
            return 20
        return None

    def get_template_names(self):
        """
        Dynamicky volí šablonu podle toho, zda je uživatel na PC nebo mobilu.
        """
        if get_user_agent(self.request).is_pc:
            return ['hpm_sklad/sklad.html']
        return ['hpm_sklad/sklad_mobile.html']

    def get_context_data(self, **kwargs):
        """
        Přidává další data do kontextu pro zobrazení v šabloně.

        Vrací:
        - Kontext obsahující filtry, řazení a vybranou položku skladu.
        """
        context = super().get_context_data(**kwargs)
        selected_ev_cislo = self.request.GET.get('selected', None)

        if selected_ev_cislo:
            context['selected_item'] = get_object_or_404(Sklad, evidencni_cislo=selected_ev_cislo)
        else:
            context['selected_item'] = None

        zarizeni_qs = Zarizeni.objects.all()
        zarizeni_choices = [("", "VŠE")] + [(z.kod_zarizeni, z.nazev_zarizeni) for z in zarizeni_qs]

        context.update({
            'db_table': 'sklad',
            'sort': self.request.GET.get('sort', 'evidencni_cislo'),
            'order': self.request.GET.get('order', 'down'),
            'query': self.request.GET.get('query', ''),
            'kriticky_dil': self.request.GET.get('kriticky_dil', ''),
            'ucetnictvi': self.request.GET.get('ucetnictvi', ''),
            'pod_minimem': self.request.GET.get('pod_minimem', ''),
            'zarizeni_filter': self.request.GET.get('zarizeni_filter', 'VŠE'),
            'zarizeni_choices': zarizeni_choices,
            'current_user': self.request.user,
        })

        return context

    def get_queryset(self):
        """
        Získává seznam položek skladu na základě vyhledávání a filtrování.

        Vrací:
        - queryset: Filtrovaný a seřazený seznam skladových položek.
        """
        queryset = Sklad.objects.prefetch_related('zarizeni')
        # přidání sloupce pod_minimem_sql pro filtrování položek pod minimem přímo v querysetu
        queryset = queryset.annotate(
            pod_minimem_sql=Case(
                When(mnozstvi__lt=F('min_mnozstvi_ks'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )

        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'evidencni_cislo')
        order = self.request.GET.get('order', 'down')
        filters = {
            'kriticky_dil': self.request.GET.get('kriticky_dil'),
            'ucetnictvi': self.request.GET.get('ucetnictvi'),
            'pod_minimem_sql': self.request.GET.get('pod_minimem')
        }
        zarizeni_filter = self.request.GET.get('zarizeni_filter','VŠE')

        if query:
            queryset = queryset.filter(
                Q(evidencni_cislo__icontains=query) | Q(interne_cislo__icontains=query) | Q(nazev_dilu__icontains=query)
            )

        for field, value in filters.items():
            if value == 'on':
                queryset = queryset.filter(**{field: True})

        if zarizeni_filter and zarizeni_filter != 'VŠE':
            queryset = queryset.filter(zarizeni__kod_zarizeni__iexact=zarizeni_filter)   

        if order == 'down':
            sort = f"-{sort}"
        queryset = queryset.order_by(sort)

        return queryset

    def export_to_csv(self, queryset):
        """
        Exportuje seznam skladových položek do CSV.

        Vrací:
        - HttpResponse s CSV souborem.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sklad_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Evidenční číslo', 'Číslo karty', 'Objednáno?', 'Název dílu', 'Minimum', 'Množství', 'Jednotky', 
            'Umístění', 'Dodavatel', 'Datum nákupu', 'Číslo objednávky', 'EUR/jednotka', 'Celkem EUR', 
            'Poznámka', 'Účetnictví', 'Kritický díl', 'Zařízení'
        ])

        for item in queryset:
            writer.writerow([
                item.evidencni_cislo, 
                item.interne_cislo, 
                item.objednano, 
                item.nazev_dilu, 
                item.min_mnozstvi_ks, 
                item.mnozstvi, 
                item.jednotky, 
                item.umisteni, 
                item.dodavatel, 
                item.datum_nakupu, 
                item.cislo_objednavky, 
                item.jednotkova_cena_eur, 
                item.celkova_cena_eur, 
                item.poznamka, 
                item.ucetnictvi, 
                item.kriticky_dil, 
                ', '.join([z.kod_zarizeni.upper() for z in item.zarizeni.all()])
            ])

        return response

    def render_to_response(self, context, **response_kwargs):
        """
        Určuje, zda vrátit CSV nebo HTML stránku, na základě parametrů.

        Vrací:
        - HttpResponse s HTML nebo CSV obsahem.
        """
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        return super().render_to_response(context, **response_kwargs)    


class SkladCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vytváří novou položku ve skladu.

    - Povoleno pouze uživatelům s oprávněním 'add_sklad'.
    
    Template:
    - `create_sklad.html`

    Po úspěšném vytvoření:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Sklad
    form_class = SkladCreateForm
    template_name = 'hpm_sklad/create_sklad.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.add_sklad'

    def get(self, request, *args, **kwargs):
        logger.info(f"{request.user} otevřel formulář pro vytvoření nové skladové položky")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info(f"{request.user} odeslal POST požadavek pro vytvoření nové skladové položky")
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Chyba při vytváření nové položky: {e}")
            raise

    def form_valid(self, form):
        self.object = form.save()
        logger.info(f"{self.request.user} vytvořil novou skladovou položku: {self.object}")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"{self.request.user} odeslal neplatný formulář pro vytvoření skladové položky.")
        logger.debug(f"Formulářové chyby: {form.errors}")
        return super().form_invalid(form)

    def handle_no_permission(self):
        logger.warning(f'Neoprávněný přístup uživatele {self.request.user} k vytvoření nové položky')
        return super().handle_no_permission()    
      
    def get_context_data(self, **kwargs):
        """
        Přidává vybranou položku do kontextu šablony.
        """
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('pk', None)
        if selected_id:
            context['skladova_polozka'] = get_object_or_404(Sklad, evidencni_cislo=selected_id)
            logger.debug(f"Přidána skladová položka do kontextu: ID {selected_id}")            
        return context       


class SkladUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Aktualizuje existující položku ve skladu.

    - Povoleno pouze uživatelům s oprávněním 'change_sklad'.
    
    Template:
    - `update_sklad.html`

    Po úspěšné aktualizaci:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Sklad
    form_class = SkladUpdateForm    
    template_name = 'hpm_sklad/update_sklad.html'
    permission_required = 'hpm_sklad.change_sklad'
    success_url = reverse_lazy('sklad')

    def get(self, request, *args, **kwargs):
        logger.info(f"{request.user} otevřel formulář pro úpravu skladové položky #{kwargs.get('pk')}")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info(f"{request.user} odeslal POST pro úpravu skladové položky #{kwargs.get('pk')}")
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Chyba při zpracování POST požadavku: {e}")
            raise    

    def handle_no_permission(self):
        logger.warning(f'Neoprávněný přístup uživatele {self.request.user} ke stránce pro úpravu skladové položky')
        return super().handle_no_permission()
    
    def form_valid(self, form):
        sklad = form.save(commit=False)
        logger.info(f"{self.request.user} odeslal platný formulář a uložil změny pro skladovou položku: {sklad}")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"{self.request.user} odeslal neplatný formulář pro úpravu skladové položky #{self.get_object().pk}")
        logger.debug(f"Form errors: {form.errors}")
        return super().form_invalid(form)
    
    
class SkladUpdateObjednanoView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Aktualizuje stav položky 'objednáno' ve skladu.

    Template:
    - `update_objednano_sklad.html`

    Po úspěšné aktualizaci:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Sklad
    form_class = SkladUpdateObjednanoForm    
    template_name = 'hpm_sklad/update_objednano_sklad.html'
    permission_required = 'hpm_sklad.change_objednano_in_sklad'
    success_url = reverse_lazy('sklad')

    def get(self, request, *args, **kwargs):
        logger.info(f"{request.user} otevřel formulář pro úpravu sloupce Objednáno? skladové položky #{kwargs.get('pk')}")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info(f"{request.user} odeslal POST pro úpravu sloupce Objednáno? skladové položky #{kwargs.get('pk')}")
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Chyba při zpracování POST požadavku: {e}")
            raise    

    def handle_no_permission(self):
        logger.warning(f'Neoprávněný přístup uživatele {self.request.user} ke stránce pro úpravu sloupce Objednáno? skladové položky')
        return super().handle_no_permission()    
    
    def form_valid(self, form):
        sklad = form.save(commit=False)
        logger.info(f"{self.request.user} odeslal platný formulář a uložil změny sloupce Objednáno? pro skladovou položku: {sklad}")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"{self.request.user} odeslal neplatný formulář pro úpravu sloupce Objednáno? skladové položky #{self.get_object().pk}")
        logger.debug(f"Form errors: {form.errors}")
        return super().form_invalid(form)


class SkladDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Maže existující položku ve skladu.

    - Povoleno pouze uživatelům s oprávněním 'delete_sklad'.
    
    Template:
    - `delete_sklad.html`

    Po úspěšném smazání:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Sklad
    template_name = 'hpm_sklad/delete_sklad.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.delete_sklad'
    

class SkladDetailView(LoginRequiredMixin, DetailView):
    """
    Zobrazuje detailní informace o skladové položce.

    Template:
    - 'detail_sklad.html'
    
    Kontext:
    - Zahrnuje detaily skladové položky, seznam variant a pole přiřazených zařízení.
    """
    model = Sklad
    template_name = 'hpm_sklad/detail_sklad.html'

    def get_context_data(self, **kwargs):
        """
        Přidává detaily skladové položky do kontextu šablony.

        Vrací:
        - Kontext obsahující pole položek, varianty a atributy zařízení.
        """
        context = super().get_context_data(**kwargs)
        varianty = self.object.varianty_skladu.all()      
        zarizeni = self.object.zarizeni.all()  

        equipment_fields = [z.kod_zarizeni for z in zarizeni]

        info_fields = [field for field in Sklad._meta.fields if field.name in ('ucetnictvi', 'kriticky_dil')]
        info_fields.append({'verbose_name': 'Pod minimem', 'name': 'pod_minimem'})

        detail_item_fields = [
            field for field in Sklad._meta.fields
            if field.name not in ('nazev_dilu', 'ucetnictvi', 'kriticky_dil')
        ]

        context['equipment_fields'] = equipment_fields
        context['info_fields'] = info_fields
        context['detail_item_fields'] = detail_item_fields
        context['varianty'] = varianty      
        return context


class AuditLogListView(LoginRequiredMixin, ListView):
    """
    Zobrazuje seznam záznamů audit logu.

    - Povoleno pouze přihlášeným uživatelům.
    - Umožňuje stránkování a export do CSV nebo grafu.

    Template:
    - `audit_log.html`

    Kontext:
    - Seznam záznamů logu, filtry a řazení.
    """
    model = AuditLog
    template_name = 'hpm_sklad/audit_log.html' 
    paginate_by = 20
    export_csv = False
    graph = False
    graph_type_of_maintenance = False

    def get_context_data(self, **kwargs):
        """
        Přidává další data do kontextu pro zobrazení v šabloně.

        Vrací:
        - Kontext obsahující filtry, roky a další informace.
        """
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('selected', None)

        if selected_id:
            context['selected_item'] = get_object_or_404(AuditLog, id=selected_id)
        else:
            context['selected_item'] = None

        current_year = datetime.datetime.now().year
        context['years'] = range(current_year, 2023, -1)

        context.update({
            'db_table': 'audit_log',
            'sort': self.request.GET.get('sort', 'id'),
            'order': self.request.GET.get('order', 'down'),
            'query': self.request.GET.get('query', ''),
            'typ_operace': self.request.GET.get('typ_operace', 'VŠE'),
            'typ_udrzby': self.request.GET.get('typ_udrzby', 'VŠE'),
            'month': self.request.GET.get('month', 'VŠE'),
            'year': self.request.GET.get('year', 'VŠE'),
            'ucetnictvi': self.request.GET.get('ucetnictvi', ''),
            'current_user': self.request.user,            
        })

        return context    

    def get_queryset(self):
        """
        Získává seznam audit logů na základě vyhledávání, filtrování, ročních a měsíčních kritérií.

        Vrací:
        - queryset: Filtrovaný a seřazený seznam záznamů.
        """
        queryset = AuditLog.objects.all()
        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'id')
        order = self.request.GET.get('order', 'down')
        typ_operace = self.request.GET.get('typ_operace', 'VŠE')
        typ_udrzby = self.request.GET.get('typ_udrzby', 'VŠE')
        self.month = self.request.GET.get('month', 'VŠE')
        self.year = self.request.GET.get('year', 'VŠE')

        if query:
            queryset = queryset.filter(
                Q(nazev_dilu__icontains=query) | Q(dodavatel__icontains=query)
            )

        if self.request.GET.get('ucetnictvi', '') == 'on':
            queryset = queryset.filter(ucetnictvi=True)
        
        if typ_operace != 'VŠE':
            queryset = queryset.filter(typ_operace=typ_operace)

        if typ_udrzby != 'VŠE':
            queryset = queryset.filter(typ_udrzby=typ_udrzby)

        if self.month != 'VŠE':
            queryset = queryset.filter(
                Q(datum_vydeje__month=self.month) | Q(datum_nakupu__month=self.month)
            )

        if self.year != 'VŠE':
            queryset = queryset.filter(
                Q(datum_vydeje__year=self.year) | Q(datum_nakupu__year=self.year)
            )

        if order == 'down':
            sort = f"-{sort}"
        queryset = queryset.order_by(sort)

        return queryset

    def export_to_csv(self, queryset):
        """
        Exportuje seznam záznamů audit logu do CSV.

        Vrací:
        - HttpResponse s CSV souborem.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_log_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Účetnictví', 'Evidenční číslo', 'Číslo karty', 'Objednáno?', 'Název dílu', 'Změna množství', 
            'Množství', 'Jednotky', 'Typ operace', 'Pro zařízení', 'Umístění', 'Dodavatel', 
            'Datum výdeje', 'Datum nákupu', 'Číslo objednávky', 'EUR/jednotka', 'Celkem EUR', 
            'Čas vytvoření', 'Operaci provedl', 'Typ údržby', 'Poznámka'
        ])

        for item in queryset:
            writer.writerow([
                item.ucetnictvi, 
                item.evidencni_cislo_id,  
                item.interne_cislo, 
                item.objednano, 
                item.nazev_dilu, 
                item.zmena_mnozstvi, 
                item.mnozstvi, 
                item.jednotky, 
                item.typ_operace, 
                item.pouzite_zarizeni, 
                item.umisteni, 
                item.dodavatel, 
                item.datum_vydeje, 
                item.datum_nakupu, 
                item.cislo_objednavky, 
                item.jednotkova_cena_eur, 
                item.celkova_cena_eur, 
                item.cas_vytvoreni, 
                item.operaci_provedl.username, 
                item.typ_udrzby,
                item.poznamka
            ])

        return response

    def generate_graph_to_pdf(self, queryset):
        """
        Generuje graf z audit logu a ukládá ho do PDF souboru.

        Vrací:
        - FileResponse obsahující graf ve formátu PDF.
        """
        # Připraví data pro graf
        data = {}
        for item in queryset:
            if item.typ_operace == 'VÝDEJ':
                if item.pouzite_zarizeni not in data:
                    data[item.pouzite_zarizeni] = 0
                data[item.pouzite_zarizeni] += abs(item.celkova_cena_eur)
        
        zarizeni = sorted(data.keys())
        naklady = [data[key] for key in zarizeni]

        # Vytvoří graf pomocí matplotlib
        plt.figure(figsize=(14, 8))  # Zvýšení velikosti obrázku
        plt.bar(zarizeni, naklady, color='skyblue')
        plt.xlabel('Zařízení')
        plt.ylabel('EUR')
        plt.title(f"Náklady za období: měsíc:{self.month}, rok:{self.year}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Uloží graf do bufferu
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Načte obrázek z bufferu pomocí Pillow
        image = Image.open(buf)

        # Připraví PDF pomocí reportlab
        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        p.drawString(100, 560, "Náklady na náhradní díly")  # Úprava pozice textu

        # Použije ImageReader pro přidání obrázku do PDF
        img_reader = ImageReader(image)
        p.drawImage(img_reader, 50, 150, width=700, height=400)  # Úprava velikosti a pozice obrázku

        p.showPage()
        p.save()
        pdf_buffer.seek(0)

        return FileResponse(pdf_buffer, as_attachment=True, filename='graf_naklady_na_zarizeni.pdf')
    
    def generate_graph_by_maintenance(self, queryset):
        """
        Generuje graf nákladů podle typu údržby za zvolený měsíc a rok a ukládá ho do PDF souboru.

        Vrací:
        - FileResponse obsahující graf ve formátu PDF.
        """
        # Připraví data pro graf
        data = {}
        for item in queryset:
            if item.typ_udrzby not in data:
                data[item.typ_udrzby] = 0
            data[item.typ_udrzby] += abs(item.celkova_cena_eur)

        typy_udrzby = sorted(data.keys())
        naklady = [data[key] for key in typy_udrzby]

        # Vytvoří graf pomocí matplotlib
        plt.figure(figsize=(14, 8))  # Zvýšení velikosti obrázku
        plt.bar(typy_udrzby, naklady, color='lightgreen')
        plt.xlabel('Typ údržby')
        plt.ylabel('EUR')
        plt.title(f"Náklady podle typu údržby: měsíc {self.month}, rok {self.year}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Uloží graf do bufferu
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Načte obrázek z bufferu pomocí Pillow
        image = Image.open(buf)

        # Připraví PDF pomocí reportlab
        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=landscape(letter))
        p.drawString(100, 560, "Náklady podle typu údržby")  # Úprava pozice textu

        # Použije ImageReader pro přidání obrázku do PDF
        img_reader = ImageReader(image)
        p.drawImage(img_reader, 50, 150, width=700, height=400)  # Úprava velikosti a pozice obrázku

        p.showPage()
        p.save()
        pdf_buffer.seek(0)

        return FileResponse(pdf_buffer, as_attachment=True, filename='graf_naklady_podle_typu_udrzby.pdf')


    def render_to_response(self, context, **response_kwargs):
        """
        Určuje, zda vrátit CSV, PDF nebo HTML stránku, na základě atributů.

        Vrací:
        - HttpResponse s HTML, CSV nebo PDF obsahem.
        """
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        elif getattr(self, 'graph_type_of_maintenance', False):
            # Vykreslí graf nákladů dle typu údržby
            return self.generate_graph_by_maintenance(self.get_queryset())
        elif getattr(self, 'graph', False):
            # Vykreslí výchozí graf
            return self.generate_graph_to_pdf(self.get_queryset())
        else:
            return super().render_to_response(context, **response_kwargs)
        


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """
    Zobrazuje detailní informace o záznamu v audit logu.

    Template:
    - `detail_audit_log.html`
    
    Kontext:
    - Detaily vybraného záznamu v audit logu.
    """
    model = AuditLog
    template_name = 'hpm_sklad/detail_audit_log.html'

    def get_context_data(self, **kwargs):
        """
        Přidává detaily záznamu do kontextu šablony.

        Vrací:
        - Kontext obsahující detailní položky audit logu.
        """
        context = super().get_context_data(**kwargs)
        context['detail_item_fields'] = self.model._meta.get_fields()
        return context


class AuditLogShowView(LoginRequiredMixin, ListView):
    """
    Zobrazuje omezený seznam záznamů audit logu pro vybranou položku skladu.

    - Povoleno pouze přihlášeným uživatelům.

    Template:
    - `show_audit_log.html`

    Kontext:
    - Zahrnuje audit logy pro vybranou položku skladu a informaci o tom, zda existuje více než 22 záznamů.
    """    
    model = AuditLog
    template_name = 'hpm_sklad/show_audit_log.html' 

    def get_context_data(self, **kwargs):
        """
        Přidává do kontextu aktuální položku skladu a informaci, zda existuje více než 22 záznamů.

        Vrací:
        - Kontext obsahující zvolený záznam skladu a stav, zda existuje více položek než 22.
        """
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('pk', None)
        context['object'] = get_object_or_404(Sklad, pk=selected_id)
        context['more_items'] = self.filtered_count > 22
        return context    

    def get_queryset(self):
        """
        Získává omezený seznam audit logů podle vybrané položky skladu.

        - Pokud je v URL přítomný primární klíč (`pk`), filtrace proběhne podle evidenčního čísla (`evidencni_cislo_id`).
        - Omezí počet vrácených záznamů na 22.

        Vrací:
        - queryset: Omezený seznam audit logů pro vybranou položku skladu.
        """
        queryset = AuditLog.objects.all()
        selected_id = self.request.GET.get('pk', None)
        if selected_id:
            queryset = queryset.filter(evidencni_cislo_id=selected_id)
        self.filtered_count = queryset.count()
        return queryset[:22]
    
    
class VariantyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vytváří novou variantu skladové položky.

    - Povoleno pouze uživatelům s oprávněním 'add_varianty'.

    Template:
    - `create_varianty.html`

    Po úspěšném vytvoření:
    - Přesměruje uživatele zpět na seznam skladových položek.
    """
    model = Varianty
    form_class = VariantyCreateForm
    template_name = 'hpm_sklad/create_varianty.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.add_varianty'

    def get_context_data(self, **kwargs):
        """
        Přidává skladovou položku do kontextu šablony.
        """
        context = super().get_context_data(**kwargs)
        context['skladova_polozka'] = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        return context

    def get_form(self, form_class=None):
        """
        Přizpůsobuje formulář tak, aby vyloučil dodavatele, kteří již mají přiřazenou variantu pro tuto skladovou položku.
        """
        form = super().get_form(form_class)
        skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        
        # Získání dodavatelů, kteří ještě nemají variantu pro danou skladovou položku
        existing_dodavatele_ids = Varianty.objects.filter(sklad=skladova_polozka).values_list('dodavatel', flat=True)
        form.fields['dodavatel'].queryset = Dodavatele.objects.exclude(pk__in=existing_dodavatele_ids)
        
        return form    

    def form_valid(self, form):
        """
        Validuje a uloží novou variantu skladové položky.
        """
        form.instance.sklad = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        return super().form_valid(form)


class VariantyWithDodavatelCreateView(CreateView):
    """
    Vytváří novou variantu skladové položky s předdefinovaným dodavatelem.

    Template:
    - `create_varianty_with_dodavatel.html`

    Kontext:
    - Skladová položka a dodavatel z kontextu URL.

    Po úspěšném vytvoření:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Varianty
    form_class = VariantyCreateForm
    template_name = 'hpm_sklad/create_varianty_with_dodavatel.html'
    success_url = reverse_lazy('sklad')

    def get_initial(self):
        """
        Inicializuje hodnoty pro pole formuláře, včetně dodavatele.
        """
        initial = super().get_initial()
        dodavatel_id = self.kwargs.get('dodavatel')
        if dodavatel_id:
            initial['dodavatel'] = Dodavatele.objects.get(id=dodavatel_id)
        return initial

    def get_context_data(self, **kwargs):
        """
        Přidává dodavatele a skladovou položku do kontextu šablony.
        """
        context = super().get_context_data(**kwargs)
        dodavatel_id = self.kwargs.get('dodavatel')
        skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs.get('pk'))
        context['skladova_polozka'] = skladova_polozka
        if dodavatel_id:
            dodavatel_object = Dodavatele.objects.get(id=dodavatel_id)
            context['dodavatel'] = dodavatel_object
            context['dodavatel_id'] = dodavatel_id  # Dodání ID do kontextu
        return context

    def form_valid(self, form):
        """
        Přiřazuje skladovou položku k vytvořené variantě a validuje formulář.
        """
        skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        form.instance.sklad = skladova_polozka

        # Kontrola, zda varianta se stejným dodavatelem již existuje
        if Varianty.objects.filter(sklad=skladova_polozka, dodavatel=form.instance.dodavatel).exists():
            form.add_error('dodavatel', 'Varianta se stejným dodavatelem již existuje.')
            return self.form_invalid(form) 
          
        return super().form_valid(form)


class VariantyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Aktualizuje existující variantu skladové položky.

    - Povoleno pouze uživatelům s oprávněním 'change_varianty'.

    Template:
    - `update_varianty.html`

    Po úspěšné aktualizaci:
    - Přesměruje uživatele zpět na seznam skladů.
    """
    model = Varianty
    form_class = VariantyUpdateForm
    template_name = 'hpm_sklad/update_varianty.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.update_varianty'

    def get_context_data(self, **kwargs):
        """
        Přidává skladovou položku do kontextu šablony.
        """
        context = super().get_context_data(**kwargs)
        varianta = self.get_object()
        context['skladova_polozka'] = varianta.sklad
        return context


class DodavateleListView(LoginRequiredMixin, ListView):
    """
    Zobrazuje seznam dodavatelů.

    Template:
    - `dodavatele.html`

    Kontext:
    - Seznam dodavatelů a možnosti filtrování.
    """
    model = Dodavatele
    template_name = 'hpm_sklad/dodavatele.html'
    paginate_by = 20
    export_csv = False

    def get_context_data(self, **kwargs):
        """
        Přidává další data do kontextu pro zobrazení v šabloně.

        Vrací:
        - Kontext obsahující filtry, řazení a aktuálně vybraného dodavatele.
        """
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('selected', None)

        if selected_id:
            context['selected_item'] = get_object_or_404(Dodavatele, id=selected_id)
        else:
            context['selected_item'] = None

        context.update({
            'db_table': 'dodavatele',
            'sort': self.request.GET.get('sort', 'id'),
            'order': self.request.GET.get('order', 'down'),
            'query': self.request.GET.get('query', ''),
            'current_user': self.request.user,
        })

        return context

    def get_queryset(self):
        """
        Získává seznam dodavatelů na základě vyhledávání a filtrování.

        Vrací:
        - queryset: Filtrovaný a seřazený seznam dodavatelů.
        """
        queryset = Dodavatele.objects.all()
        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'id')
        order = self.request.GET.get('order', 'down')

        if query:
            queryset = queryset.filter(
                Q(dodavatel__icontains=query) | Q(kontakt__icontains=query)
            )

        if order == 'down':
            sort = f"-{sort}"
            
        queryset = queryset.order_by(sort)

        return queryset

    def export_to_csv(self, queryset):
        """
        Exportuje seznam dodavatelů do CSV.

        Vrací:
        - HttpResponse s CSV souborem.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dodavatele_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Dodavatel', 'Kontaktní osoba', 'E-mail', 'Telefon', 'Jazyk', 
        ])

        for item in queryset:
            writer.writerow([
                item.id, 
                item.dodavatel, 
                item.kontakt, 
                item.email, 
                item.telefon, 
                item.jazyk, 
            ])

        return response

    def render_to_response(self, context, **response_kwargs):
        """
        Určuje, zda vrátit CSV nebo HTML stránku, na základě parametrů.

        Vrací:
        - HttpResponse s HTML nebo CSV obsahem.
        """
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        else:
            return super().render_to_response(context, **response_kwargs)


class DodavateleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vytváří nového dodavatele.

    - Povoleno pouze uživatelům s oprávněním 'add_dodavatele'.

    Template:
    - `create_dodavatele.html`

    Po úspěšném vytvoření:
    - Přesměruje uživatele zpět na seznam dodavatelů.
    """
    model = Dodavatele
    form_class = DodavateleCreateForm
    template_name = 'hpm_sklad/create_dodavatele.html'
    success_url = reverse_lazy('dodavatele')
    permission_required = 'hpm_sklad.add_dodavatele'
       
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('pk', None)
        context['dodavatel'] = get_object_or_404(Dodavatele, id=selected_id)
        return context       


class DodavateleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Aktualizuje existujícího dodavatele.

    - Povoleno pouze uživatelům s oprávněním 'change_dodavatele'.

    Template:
    - `update_dodavatele.html`

    Po úspěšné aktualizaci:
    - Přesměruje uživatele zpět na seznam dodavatelů.
    """
    model = Dodavatele
    form_class = DodavateleUpdateForm    
    template_name = 'hpm_sklad/update_dodavatele.html'
    permission_required = 'hpm_sklad.change_dodavatele'
    success_url = reverse_lazy('dodavatele')

    
class DodavateleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Maže existujícího dodavatele.

    - Povoleno pouze uživatelům s oprávněním 'delete_dodavatele'.

    Template:
    - `delete_dodavatele.html`

    Po úspěšném smazání:
    - Přesměruje uživatele zpět na seznam dodavatelů.
    """
    model = Dodavatele
    template_name = 'hpm_sklad/delete_dodavatele.html'
    success_url = reverse_lazy('dodavatele')
    permission_required = 'hpm_sklad.delete_dodavatele'        



class DodavateleDetailView(LoginRequiredMixin, DetailView):
    """
    Zobrazuje detailní informace o dodavateli.

    Template:
    - Určeno buď atributem `template_name`, nebo vyvolá chybu pokud není nastaveno.

    Kontext:
    - Zahrnuje detaily dodavatele, varianty a poptávky spojené s dodavatelem.
    """
    model = Dodavatele

    def get_template_names(self):
        """
        Určuje šablonu pro zobrazení detailu dodavatele.
        Pokud není nastavena, vyvolá chybu.

        Vrací:
        - Název šablony (str).
        """
        if self.template_name:
            return [self.template_name]
        else:
            raise ValueError("Šablona není zadána")

    def get_context_data(self, **kwargs):
        """
        Přidává detaily dodavatele a jeho varianty a poptávky do kontextu šablony.

        Vrací:
        - Kontext obsahující detailní položky dodavatele, varianty a poptávky.
        """
        context = super().get_context_data(**kwargs)
        varianty = self.object.varianty_dodavatele.all()
        poptavky = self.object.poptavky_dodavatele.all()
        detail_item_fields = [
            field for field in self.model._meta.get_fields()
            if not (field.many_to_many or field.one_to_many or field.one_to_one)
            ]
        
        context['detail_item_fields'] = detail_item_fields
        context['varianty'] = varianty      
        context['poptavky'] = poptavky
        return context


@login_required
##@permission_required('hpm_sklad.add_poptavky')
def create_poptavka(request, dodavatel_id):
    """
    Vytváří novou poptávku pro daného dodavatele.

    Parameters:
    - request: HTTP request objekt.
    - dodavatel_id: Primární klíč dodavatele, pro kterého je poptávka vytvářena.

    POST:
    - Zpracuje inline formulář pro výběr variant dodavatele.
    - Pokud jsou vybrány varianty, uloží poptávku.

    GET:
    - Zobrazí prázdný formulář pro výběr variant.

    Vrací:
    - render: HTML stránku `create_poptavka.html` s formuláři a daty.
    """
    dodavatel = get_object_or_404(Dodavatele, id=dodavatel_id)
    varianty_dodavatele = Varianty.objects.filter(dodavatel_id=dodavatel_id)
    
    PoptavkaVariantyFormSet = inlineformset_factory(
        Poptavky, PoptavkaVarianty, form=PoptavkaVariantyForm, extra=varianty_dodavatele.count(), can_delete=False
        )    

    if request.method == 'POST':
        formset = PoptavkaVariantyFormSet(request.POST, form_kwargs={'varianty_dodavatele': varianty_dodavatele})
        if formset.is_valid():
            any_should_save = False
            for form in formset:
                if form.cleaned_data.get('should_save'):
                    any_should_save = True
                    break
                
            if any_should_save:
                poptavka = Poptavky.objects.create(
                    dodavatel=dodavatel,
                    stav='Tvorba',
                )
                for form in formset:
                    if form.cleaned_data.get('should_save'):
                        poptavka_varianty = form.save(commit=False)
                        poptavka_varianty.poptavka = poptavka
                        poptavka_varianty.save()
                return redirect('poptavky')
            else:
                for form, varianta_dodavatele in zip(formset.forms, varianty_dodavatele):
                    form.fields['varianta'].initial = varianta_dodavatele
                    form.fields['jednotky'].initial = varianta_dodavatele.sklad.jednotky             
                formset.non_form_errors().append('Musíte vybrat alespoň jednu položku k uložení do poptávky.')
    else:
        formset = PoptavkaVariantyFormSet(queryset=PoptavkaVarianty.objects.none(), form_kwargs={'varianty_dodavatele': varianty_dodavatele})
        for form, varianta_dodavatele in zip(formset.forms, varianty_dodavatele):
            form.fields['varianta'].initial = varianta_dodavatele
            difference = (varianta_dodavatele.sklad.min_mnozstvi_ks -
                          varianta_dodavatele.sklad.mnozstvi)
            form.fields['mnozstvi'].initial = max(difference, 0)
            form.fields['jednotky'].initial = varianta_dodavatele.sklad.jednotky
            if difference > 0:
                form.fields['should_save'].initial = True
        
    context = {'current_user': request.user, 'formset': formset, 'dodavatel': dodavatel,
               'varianty_dodavatele': varianty_dodavatele}
    return render(request, 'hpm_sklad/create_poptavka.html', context)


class PoptavkaListView(LoginRequiredMixin, ListView):
    """
    Zobrazuje seznam poptávek.

    - Povoleno pouze přihlášeným uživatelům.
    - Stránkuje výsledky a umožňuje export do CSV.

    Template:
    - `poptavky.html`

    Kontext:
    - Zahrnuje poptávky, možnosti filtrování, řazení a vyhledávání.
    """
    model = Poptavky
    template_name = 'hpm_sklad/poptavky.html'
    paginate_by = 20
    export_csv = False

    def get_context_data(self, **kwargs):
        """
        Přidává do kontextu informace o aktuálně vybrané poptávce a uživatelských filtrech.

        Vrací:
        - Kontext obsahující vybraného dodavatele, možnosti filtrování, řazení a uživatele.
        """
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('selected', None)

        if selected_id:
            context['selected_item'] = get_object_or_404(Dodavatele, id=selected_id)
        else:
            context['selected_item'] = None

        context.update({
            'db_table': 'poptavky',
            'sort': self.request.GET.get('sort', 'id'),
            'order': self.request.GET.get('order', 'down'),
            'query': self.request.GET.get('query', ''),
            'current_user': self.request.user,
        })

        return context

    def get_queryset(self):
        """
        Získává seznam poptávek na základě vyhledávání, filtrování a řazení.

        Vrací:
        - queryset: Filtrovaný a seřazený seznam poptávek.
        """
        queryset = Poptavky.objects.all()
        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'id')
        order = self.request.GET.get('order', 'down')

        if query:
            queryset = queryset.filter(dodavatel__icontains=query)

        if order == 'down':
            sort = f"-{sort}"
            
        queryset = queryset.order_by(sort)

        return queryset

    def export_to_csv(self, queryset):
        """
        Exportuje seznam poptávek do CSV.

        Vrací:
        - HttpResponse s CSV souborem.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="poptavky_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Dodavatel', 'Datum vytvoření', 'Stav', 'Varianty', 
        ])

        for item in queryset:
            writer.writerow([
                item.id, 
                item.dodavatel, 
                item.datum_vytvoreni, 
                item.stav, 
                item.varianty, 
            ])

        return response

    def render_to_response(self, context, **response_kwargs):
        """
        Určuje, zda vrátit CSV nebo HTML stránku, na základě parametrů.

        Vrací:
        - HttpResponse s HTML nebo CSV obsahem.
        """
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        else:
            return super().render_to_response(context, **response_kwargs)        


class PoptavkaDetailView(LoginRequiredMixin, DetailView):
    """
    Zobrazuje detailní informace o poptávce.

    Template:
    - `detail_poptavky.html`

    Kontext:
    - Zahrnuje detailní informace o poptávce.
    """
    model = Poptavky
    template_name = 'hpm_sklad/detail_poptavky.html'

    def get_context_data(self, **kwargs):
        """
        Přidává do kontextu detailní položky poptávky.

        Vrací:
        - Kontext obsahující pole modelu poptávky.
        """
        context = super().get_context_data(**kwargs)
        context['detail_item_fields'] = self.model._meta.get_fields()
        return context


class PoptavkaVariantyListView(LoginRequiredMixin, ListView):
    """
    Zobrazuje seznam variant poptávky pro konkrétní poptávku.

    - Povoleno pouze přihlášeným uživatelům.

    Template:
    - `poptavka_varianty.html`

    Kontext:
    - Zahrnuje varianty pro konkrétní poptávku.
    """
    model = PoptavkaVarianty
    template_name = 'hpm_sklad/poptavka_varianty.html'

    def get(self, request, *args, **kwargs):
        """
        Získává ID poptávky z URL a ukládá ho pro použití v dalších metodách.
        """
        self.poptavka_id = self.kwargs.get('pk')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Přidává ID poptávky do kontextu šablony.

        Vrací:
        - Kontext obsahující ID poptávky.
        """
        context = super().get_context_data(**kwargs)
        context['poptavka_id'] = self.poptavka_id
        return context

    def get_queryset(self):
        """
        Získává seznam variant pro konkrétní poptávku na základě ID poptávky.

        Vrací:
        - queryset: Filtrovaný seznam variant pro konkrétní poptávku.
        """
        queryset = PoptavkaVarianty.objects.filter(poptavka_id=self.poptavka_id)
        return queryset     


class CustomPasswordChangeView(PasswordChangeView):
    """
    Změní heslo uživatele pomocí formuláře.

    Template:
    - `password_change.html`

    Po úspěšné změně:
    - Přesměruje uživatele na stránku home.
    """
    success_url = reverse_lazy("home")  
    template_name = "registration/password_change.html"
  
  
def logout_request(request):
    """
    Odhlásí uživatele a přesměruje ho na úvodní stránku.

    Parameters:
    - request: HTTP request objekt.

    Vrací:
    - redirect: Přesměrování na úvodní stránku.
    """
    logout(request)
    return redirect("home")
