from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q

import datetime

from .models import Sklad, AuditLog, Dodavatele, Zarizeni
from .forms import (SkladCreateForm, SkladUpdateForm, SkladUpdateObjednanoForm, SkladReceiptForm,
                    SkladDispatchForm, AuditLogReceiptForm, AuditLogDispatchForm, CustomUserCreationForm)

def home_view(request):
    return render(request, "hpm_sklad/home.html")

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
        print(f"{sklad_movement_form.is_valid()=}")
        print(f"{auditlog_dispatch_form.is_valid()=}")
        
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_ev_cislo = self.request.GET.get('selected', None)

        if selected_ev_cislo:
            context['selected_item'] = get_object_or_404(Sklad, evidencni_cislo=selected_ev_cislo)
        else:
            context['selected_item'] = None       
        return context    

    def get_queryset(self):
        queryset = Sklad.objects.all()
        query = self.request.GET.get('q')
        
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

        # Ruční filtrování pro vlastnost pod_minimem
        pod_minimem = self.request.GET.get('pod_minimem')
        if pod_minimem == 'on':
            queryset = [obj for obj in queryset if obj.pod_minimem]

        return queryset


class SkladCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Sklad
    form_class = SkladCreateForm
    template_name = 'hpm_sklad/create_sklad.html'
    success_url = reverse_lazy('sklad')
    permission_required = 'hpm_sklad.add_sklad'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        return response

class SkladUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateForm    
    template_name = 'hpm_sklad/update_sklad.html'
    permission_required = 'hpm_sklad.change_sklad'
    
class SkladUpdateObjednanoView(LoginRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateObjednanoForm    
    template_name = 'hpm_sklad/update_objednano_sklad.html'
    success_url = "/sklad/"

class SkladDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Sklad
    template_name = 'hpm_sklad/delete_sklad.html'
    success_url = "/sklad/"
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
            if field.get_internal_type() != 'BooleanField'
        ]

        context['equipment_fields_true'] = equipment_fields_true
        context['info_fields'] = info_fields
        context['detail_item_fields'] = detail_item_fields
        return context
    

class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'hpm_sklad/audit_log.html'  # Zajistěte, že tato cesta je správná
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_id = self.request.GET.get('selected', None)

        if selected_id:
            context['selected_item'] = get_object_or_404(AuditLog, id=selected_id)
        else:
            context['selected_item'] = None

        current_year = datetime.datetime.now().year
        context['years'] = range(current_year, 2022, -1)

        context.update({
            'sort': self.request.GET.get('sort', 'id'),
            'order': self.request.GET.get('order', 'up'),
            'query': self.request.GET.get('query', ''),
            'typ_operace': self.request.GET.get('typ_operace', 'VŠE'),
            'month': self.request.GET.get('month', 'VŠE'),
            'year': self.request.GET.get('year', 'VŠE')
        })

        return context    

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        query = self.request.GET.get('query', '')

        if query:
            queryset = queryset.filter(
                Q(evidencni_cislo__nazev_dilu__icontains=query) | Q(dodavatel__icontains(query))
            )
        
        typ_operace = self.request.GET.get('typ_operace', 'VŠE')
        if typ_operace != 'VŠE':
            queryset = queryset.filter(typ_operace=typ_operace)

        month = self.request.GET.get('month', 'VŠE')
        year = self.request.GET.get('year', 'VŠE')

        if month != 'VŠE' and year != 'VŠE':
            queryset = queryset.filter(
                Q(datum_vydeje__year=year, datum_vydeje__month=month) |
                Q(datum_nakupu__year=year, datum_nakupu__month=month)
            )

        sort = self.request.GET.get('sort', 'id')
        order = self.request.GET.get('order', 'up')
        if order == 'down':
            sort = f"-{sort}"
        queryset = queryset.order_by(sort)

        return queryset


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    model = AuditLog
    template_name = 'hpm_sklad/detail_audit_log.html'

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
