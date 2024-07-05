import csv
from django.http import HttpResponse, FileResponse
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.db import models
from django.forms import inlineformset_factory

import io
import logging
import datetime


import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from PIL import Image

from .models import Sklad, AuditLog, Dodavatele, Zarizeni, Varianty, Poptavky, PoptavkaVarianty
from .forms import (SkladCreateForm, SkladUpdateForm, SkladUpdateObjednanoForm, SkladReceiptForm,
                    SkladDispatchForm, AuditLogReceiptForm, AuditLogDispatchForm, CustomUserCreationForm,
                    VariantyCreateForm, VariantyUpdateForm, PoptavkaVariantyForm)

logger = logging.getLogger(__name__)

def home_view(request):
    context = {'current_user': request.user}
    return render(request, "hpm_sklad/home.html", context)

@login_required
@permission_required('hpm_sklad.change_sklad', 'hpm_sklad.add_auditlog')
def receipt_form_view(request, pk):
    sklad_instance = get_object_or_404(Sklad, pk=pk)
    if request.method == 'POST':
        sklad_movement_form = SkladReceiptForm(request.POST, instance=sklad_instance)
        auditlog_receipt_form = AuditLogReceiptForm(request.POST)
        if sklad_movement_form.is_valid() and auditlog_receipt_form.is_valid():
            
            updated_sklad = sklad_movement_form.save(commit=False)
            created_auditlog = auditlog_receipt_form.save(commit=False)
                
            created_auditlog.jednotkova_cena_eur = round(updated_sklad.jednotkova_cena_eur, 2)
            created_auditlog.celkova_cena_eur = round(created_auditlog.jednotkova_cena_eur * created_auditlog.zmena_mnozstvi, 2)
            updated_sklad.mnozstvi = sklad_instance.mnozstvi + created_auditlog.zmena_mnozstvi
            updated_sklad.celkova_cena_eur = round(sklad_instance.celkova_cena_eur + created_auditlog.celkova_cena_eur, 2)
            updated_sklad.jednotkova_cena_eur = round(updated_sklad.celkova_cena_eur / updated_sklad.mnozstvi, 2)
            created_auditlog.typ_operace = "PŘÍJEM"
            created_auditlog.ucetnictvi = updated_sklad.ucetnictvi
            created_auditlog.evidencni_cislo = updated_sklad
            created_auditlog.interne_cislo = updated_sklad.interne_cislo
            created_auditlog.objednano = updated_sklad.objednano
            created_auditlog.nazev_dilu = updated_sklad.nazev_dilu
            created_auditlog.ucetnictvi = updated_sklad.ucetnictvi
            created_auditlog.mnozstvi = updated_sklad.mnozstvi
            created_auditlog.jednotky = updated_sklad.jednotky
            created_auditlog.umisteni = updated_sklad.umisteni
            created_auditlog.dodavatel = updated_sklad.dodavatel
            created_auditlog.datum_nakupu = updated_sklad.datum_nakupu
            created_auditlog.cislo_objednavky = updated_sklad.cislo_objednavky
            created_auditlog.operaci_provedl = request.user
            created_auditlog.poznamka = updated_sklad.poznamka
            
            updated_sklad.save()            
            created_auditlog.save()

            # Získání dodavatele z formuláře
            dodavatel_form_value = sklad_movement_form.cleaned_data['dodavatel']
            dodavatel_object = Dodavatele.objects.get(dodavatel=dodavatel_form_value)

            # Kontrola, zda varianta existuje
            varianty = Varianty.objects.filter(skladova_polozka=sklad_instance)
            varianta_dodavatele = [var.dodavatel for var in varianty]
           
            if not varianty or dodavatel_object not in varianta_dodavatele:
                return redirect(reverse('create_varianty_with_dodavatel', kwargs={'pk': pk, 'dodavatel': dodavatel_object.id}))
                                           
            return redirect('audit_log')
        
    else: # GET 
        sklad_movement_form = SkladReceiptForm(instance=sklad_instance)
        auditlog_receipt_form = AuditLogReceiptForm()

    context = {
        'sklad_movement_form': sklad_movement_form,
        'auditlog_receipt_form': auditlog_receipt_form,
        'object': sklad_instance,
    }
    return render(request, 'hpm_sklad/receipt_audit_log.html', context)


@login_required
@permission_required('hpm_sklad.change_sklad', 'hpm_sklad.add_auditlog')
def dispatch_form_view(request, pk):
    sklad_instance = get_object_or_404(Sklad, pk=pk)
    if request.method == 'POST':
        sklad_movement_form = SkladDispatchForm(request.POST, instance=sklad_instance)
        auditlog_dispatch_form = AuditLogDispatchForm(request.POST, max_mnozstvi=sklad_instance.mnozstvi)
        
        if sklad_movement_form.is_valid() and auditlog_dispatch_form.is_valid():
            updated_sklad = sklad_movement_form.save(commit=False)
            created_auditlog = auditlog_dispatch_form.save(commit=False)
           
            created_auditlog.jednotkova_cena_eur = sklad_instance.jednotkova_cena_eur
            created_auditlog.celkova_cena_eur = created_auditlog.jednotkova_cena_eur * created_auditlog.zmena_mnozstvi          
            updated_sklad.mnozstvi = sklad_instance.mnozstvi - created_auditlog.zmena_mnozstvi
            updated_sklad.celkova_cena_eur = sklad_instance.celkova_cena_eur - created_auditlog.celkova_cena_eur
            created_auditlog.typ_operace = "VÝDEJ"
            created_auditlog.ucetnictvi = updated_sklad.ucetnictvi
            created_auditlog.evidencni_cislo = updated_sklad
            created_auditlog.interne_cislo = updated_sklad.interne_cislo
            created_auditlog.objednano = updated_sklad.objednano
            created_auditlog.nazev_dilu = updated_sklad.nazev_dilu
            created_auditlog.ucetnictvi = updated_sklad.ucetnictvi
            created_auditlog.mnozstvi = updated_sklad.mnozstvi
            created_auditlog.jednotky = updated_sklad.jednotky
            created_auditlog.umisteni = updated_sklad.umisteni
            created_auditlog.dodavatel = updated_sklad.dodavatel
            created_auditlog.cislo_objednavky = updated_sklad.cislo_objednavky
            created_auditlog.operaci_provedl = request.user
            created_auditlog.poznamka = updated_sklad.poznamka
            
            updated_sklad.save()            
            created_auditlog.save()
            return redirect('audit_log')
                   
    else: # GET 
        sklad_movement_form = SkladDispatchForm(instance=sklad_instance)
        auditlog_dispatch_form = AuditLogDispatchForm(max_mnozstvi=sklad_instance.mnozstvi)

    context = {
        'sklad_movement_form': sklad_movement_form,
        'auditlog_dispatch_form': auditlog_dispatch_form,
        'object': sklad_instance,
    }
    return render(request, 'hpm_sklad/dispatch_audit_log.html', context)


class SkladListView(LoginRequiredMixin, ListView):
    model = Sklad
    template_name = 'hpm_sklad/sklad.html'
    paginate_by = 20
    export_csv = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_ev_cislo = self.request.GET.get('selected', None)

        if selected_ev_cislo:
            context['selected_item'] = get_object_or_404(Sklad, evidencni_cislo=selected_ev_cislo)
        else:
            context['selected_item'] = None

        radio_filters = [("", "VŠE")] + [(z.zarizeni.lower(), z.zarizeni.replace('_', ' ')) for z in Zarizeni.objects.all()]

        context.update({
            'db_table': 'sklad',
            'sort': self.request.GET.get('sort', 'evidencni_cislo'),
            'order': self.request.GET.get('order', 'down'),
            'query': self.request.GET.get('query', ''),
            'kriticky_dil': self.request.GET.get('kriticky_dil', ''),
            'ucetnictvi': self.request.GET.get('ucetnictvi', ''),
            'pod_minimem': self.request.GET.get('pod_minimem', ''),
            'radio_filter': self.request.GET.get('radio_filter', ''),
            'radio_filters': radio_filters,
            'current_user': self.request.user,
        })

        return context

    def get_queryset(self):
        queryset = Sklad.objects.all()
        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'evidencni_cislo')
        order = self.request.GET.get('order', 'down')

        if query:
            queryset = queryset.filter(nazev_dilu__icontains=query)

        filters = {
            'kriticky_dil': self.request.GET.get('kriticky_dil'),
            'ucetnictvi': self.request.GET.get('ucetnictvi'),
        }

        for field, value in filters.items():
            if value == 'on':
                queryset = queryset.filter(**{field: True})

        radio_filter = self.request.GET.get('radio_filter')
        if radio_filter:
            queryset = queryset.filter(**{radio_filter: True})

        if order == 'down':
            sort = f"-{sort}"
        queryset = queryset.order_by(sort)

        pod_minimem = self.request.GET.get('pod_minimem')
        if pod_minimem == 'on':
            queryset = [obj for obj in queryset if obj.pod_minimem]

        return queryset

    def export_to_csv(self, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sklad_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Evidenční číslo', 'Číslo karty', 'Objednáno?', 'Název dílu', 'Minimum', 'Množství', 'Jednotky', 
            'Umístění', 'Dodavatel', 'Datum nákupu', 'Číslo objednávky', 'EUR/jednotka', 'Celkem EUR', 
            'Poznámka', 'Účetnictví', 'Kritický díl', 'HSH', 'TQ8', 'TQF XL1', 'TQF XL2', 'DC XL', 
            'DAC XL1-2', 'DL XL', 'DAC', 'LAC 1', 'LAC 2', 'IPSEN ENE', 'HSH ENE', 'XL ENE1', 
            'XL ENE2', 'IPSEN W', 'HSH W', 'KW', 'KW 1', 'KW 2', 'KW 3', 'MIKROF'
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
                item.hsh, 
                item.tq8, 
                item.tqf_xl1, 
                item.tqf_xl2, 
                item.dc_xl, 
                item.dac_xl1_2, 
                item.dl_xl, 
                item.dac, 
                item.lac_1, 
                item.lac_2, 
                item.ipsen_ene, 
                item.hsh_ene, 
                item.xl_ene1, 
                item.xl_ene2, 
                item.ipsen_w, 
                item.hsh_w, 
                item.kw, 
                item.kw1, 
                item.kw2, 
                item.kw3, 
                item.mikrof
            ])

        return response

    def render_to_response(self, context, **response_kwargs):
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        else:
            return super().render_to_response(context, **response_kwargs)    


class SkladCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Sklad
    form_class = SkladCreateForm
    template_name = 'hpm_sklad/create_sklad.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.add_sklad'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('pk', None)
        context['skladova_polozka'] = get_object_or_404(Sklad, evidencni_cislo=selected_id)
        return context       


class SkladUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateForm    
    template_name = 'hpm_sklad/update_sklad.html'
    permission_required = 'hpm_sklad.change_sklad'
    success_url = reverse_lazy('sklad')

    
class SkladUpdateObjednanoView(LoginRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateObjednanoForm    
    template_name = 'hpm_sklad/update_objednano_sklad.html'
    success_url = reverse_lazy('sklad')


class SkladDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Sklad
    template_name = 'hpm_sklad/delete_sklad.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.delete_sklad'
    

class SkladDetailView(LoginRequiredMixin, DetailView):
    model = Sklad
    template_name = 'hpm_sklad/detail_sklad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_instance = self.get_object()

        equipment_fields_true = [
            field for field in Sklad._meta.fields
            if field.get_internal_type() == 'BooleanField' and getattr(object_instance, field.name) is True and field.name not in ("ucetnictvi", "kriticky_dil")
        ]

        info_fields = [field for field in Sklad._meta.fields if field.name in ("ucetnictvi", "kriticky_dil")]
        info_fields.append({'verbose_name': 'Pod minimem', 'name': 'pod_minimem'})

        detail_item_fields = [
            field for field in Sklad._meta.fields
            if field.get_internal_type() != 'BooleanField' and field.name != 'nazev_dilu'
        ]

        context['equipment_fields_true'] = equipment_fields_true
        context['info_fields'] = info_fields
        context['detail_item_fields'] = detail_item_fields
        return context


class SkladVariantyDetailView(LoginRequiredMixin, DetailView):
    model = Sklad
    template_name = 'hpm_sklad/show_varianty.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        varianty = self.object.varianty_skladu.all()
        context['varianty'] = varianty
        return context
    

class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'hpm_sklad/audit_log.html' 
    paginate_by = 20
    export_csv = False
    graph = False

    def get_context_data(self, **kwargs):
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
            'month': self.request.GET.get('month', 'VŠE'),
            'year': self.request.GET.get('year', 'VŠE'),
            'ucetnictvi': self.request.GET.get('ucetnictvi', ''),
            'current_user': self.request.user,            
        })

        return context    

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        query = self.request.GET.get('query', '')
        sort = self.request.GET.get('sort', 'id')
        order = self.request.GET.get('order', 'down')

        if query:
            queryset = queryset.filter(
                Q(nazev_dilu__icontains=query) | Q(dodavatel__icontains=query)
            )

        if self.request.GET.get('ucetnictvi', '') == 'on':
            queryset = queryset.filter(ucetnictvi=True)
        
        typ_operace = self.request.GET.get('typ_operace', 'VŠE')
        if typ_operace != 'VŠE':
            queryset = queryset.filter(typ_operace=typ_operace)

        self.month = self.request.GET.get('month', 'VŠE')
        self.year = self.request.GET.get('year', 'VŠE')

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
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_log_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Účetnictví', 'Evidenční číslo', 'Číslo karty', 'Objednáno?', 'Název dílu', 'Změna množství', 
            'Množství', 'Jednotky', 'Typ operace', 'Pro zařízení', 'Umístění', 'Dodavatel', 
            'Datum výdeje', 'Datum nákupu', 'Číslo objednávky', 'EUR/jednotka', 'Celkem EUR', 
            'Čas vytvoření', 'Operaci provedl', 'Poznámka'
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
                item.poznamka
            ])

        return response

    def generate_graph_to_pdf(self, queryset):
        # Připraví data pro graf
        data = {}
        for item in queryset:
            if item.typ_operace == 'VÝDEJ':
                if item.pouzite_zarizeni not in data:
                    data[item.pouzite_zarizeni] = 0
                data[item.pouzite_zarizeni] -= item.celkova_cena_eur
        
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

    def render_to_response(self, context, **response_kwargs):
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        elif getattr(self, 'graph', False):
            return self.generate_graph_to_pdf(self.get_queryset())        
        else:
            return super().render_to_response(context, **response_kwargs)        


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    model = AuditLog
    template_name = 'hpm_sklad/detail_audit_log.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detail_item_fields'] = self.model._meta.get_fields()
        return context


class AuditLogShowView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'hpm_sklad/show_audit_log.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('pk', None)
        context['object'] = get_object_or_404(Sklad, pk=selected_id)
        context['more_items'] = self.filtered_count > 22
        return context    

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        selected_id = self.request.GET.get('pk', None)
        if selected_id:
            queryset = queryset.filter(evidencni_cislo_id=selected_id)
        self.filtered_count = queryset.count()
        return queryset[:22]
    
    
class VariantyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Varianty
    form_class = VariantyCreateForm
    template_name = 'hpm_sklad/create_varianty.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.add_varianty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skladova_polozka'] = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        
        # Získání dodavatelů, kteří ještě nemají variantu pro danou skladovou položku
        existing_dodavatele_ids = Varianty.objects.filter(sklad=skladova_polozka).values_list('dodavatel', flat=True)
        form.fields['dodavatel'].queryset = Dodavatele.objects.exclude(pk__in=existing_dodavatele_ids)
        
        return form    

    def form_valid(self, form):
        form.instance.skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        return super().form_valid(form)


class VariantyWithDodavatelCreateView(CreateView):
    model = Varianty
    form_class = VariantyCreateForm
    template_name = 'hpm_sklad/create_varianty_with_dodavatel.html'
    success_url = reverse_lazy('sklad')

    def get_initial(self):
        initial = super().get_initial()
        dodavatel_id = self.kwargs.get('dodavatel')
        if dodavatel_id:
            initial['dodavatel'] = Dodavatele.objects.get(id=dodavatel_id)
        return initial

    def get_context_data(self, **kwargs):
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
        skladova_polozka = get_object_or_404(Sklad, pk=self.kwargs['pk'])
        form.instance.skladova_polozka = skladova_polozka

        # Kontrola, zda varianta se stejným dodavatelem již existuje
        if Varianty.objects.filter(sklad=skladova_polozka, dodavatel=form.instance.dodavatel).exists():
            form.add_error('dodavatel', 'Varianta se stejným dodavatelem již existuje.')
            return self.form_invalid(form)    


class VariantyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Varianty
    form_class = VariantyUpdateForm
    template_name = 'hpm_sklad/update_varianty.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.update_varianty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        varianta = self.get_object()
        context['skladova_polozka'] = varianta.sklad
        return context


class DodavateleListView(LoginRequiredMixin, ListView):
    model = Dodavatele
    template_name = 'hpm_sklad/dodavatele.html'
    paginate_by = 20
    export_csv = False

    def get_context_data(self, **kwargs):
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
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dodavatele_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Dodavatel', 'Kontaktní osoba', 'E-mail', 'Telefon', 'Jazyk', 
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
        if getattr(self, 'export_csv', False):
            return self.export_to_csv(self.get_queryset())
        else:
            return super().render_to_response(context, **response_kwargs)        


class DodavateleDetailView(LoginRequiredMixin, DetailView):
    model = Dodavatele
    template_name = 'hpm_sklad/detail_dodavatele.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)               
        context['varianty'] = self.object.varianty_dodavatele.all()
        return context

@login_required
##@permission_required('hpm_sklad.add_poptavky')
def create_poptavka(request, dodavatel_id):
    dodavatel = get_object_or_404(Dodavatele, id=dodavatel_id)
    varianty_dodavatele = Varianty.objects.filter(dodavatel_id=dodavatel_id)
    
    PoptavkaVariantyFormSet = inlineformset_factory(
        Poptavky, PoptavkaVarianty, form=PoptavkaVariantyForm, extra=varianty_dodavatele.count(),
        )    

    if request.method == 'POST':
        formset = PoptavkaVariantyFormSet(request.POST, form_kwargs={'varianty_dodavatele': varianty_dodavatele})
        if formset.is_valid():
            poptavka = Poptavky.objects.create(
                dodavatel=dodavatel,
                stav='Tvorba',
            )
            for form in formset:
                if form.cleaned_data.get('should_save'):
                    poptavka_varianty = form.save(commit=False)
                    poptavka_varianty.poptavka = poptavka
                    poptavka_varianty.save()
            return redirect('detail_poptavky', pk=poptavka.pk)
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
        
    context = {'current_user': request.user, 'formset': formset, 'dodavatel': dodavatel, 'varianty_dodavatele': varianty_dodavatele}
    return render(request, 'hpm_sklad/create_poptavka.html', context)


class PoptavkaDetailView(LoginRequiredMixin, DetailView):
    model = Poptavky
    template_name = 'hpm_sklad/detail_poptavky.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detail_item_fields'] = self.model._meta.get_fields()
        return context    

    
class SignUp(CreateView):
  form_class = CustomUserCreationForm
  success_url = reverse_lazy("login")
  template_name = "registration/signup.html"   
  
  
def logout_request(request):
  logout(request)
  return redirect("home")
