from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Sklad, AuditLog
from .forms import (SkladCreateForm, SkladUpdateForm, SkladUpdateObjednanoForm,
                    SkladReceiptUpdateForm, AuditLogCreateForm, CustomUserCreationForm)

def home_view(request):
    return render(request, "hpm_sklad/home.html")

@login_required
@permission_required('hpm_sklad.change_sklad', 'hpm_sklad.add_auditlog')
def receipt_form_view(request, pk):
    sklad_instance = get_object_or_404(Sklad, pk=pk)
    if request.method == 'POST':
        sklad_receipt_form = SkladReceiptUpdateForm(request.POST, instance=sklad_instance)
        auditlog_create_form = AuditLogCreateForm(request.POST)
        
        if sklad_receipt_form.is_valid() and auditlog_create_form.is_valid():
            # Uložit změny do modelu Sklad
            updated_sklad = sklad_receipt_form.save()
            
            # Přenést data ze skladu do formuláře AuditLog
            auditlog_instance = auditlog_create_form.save(commit=False)
            auditlog_instance.evidencni_cislo = updated_sklad.evidencni_cislo
            auditlog_instance.interne_cislo = updated_sklad.interne_cislo
            auditlog_instance.save()
            
            return redirect('audit_log')
    else:
        sklad_receipt_form = SkladReceiptUpdateForm(instance=sklad_instance)
        auditlog_create_form = AuditLogCreateForm()

    context = {
        'sklad_receipt_form': sklad_receipt_form,
        'auditlog_create_form': auditlog_create_form,
        'object': sklad_instance,
    }
    return render(request, 'hpm_sklad/create_audit_log.html', context)


class SkladListView(LoginRequiredMixin, ListView):
    model = Sklad
    template_name = 'hpm_sklad/sklad.html'
    paginate_by = 20
    ordering = ['evidencni_cislo']
    
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

        return queryset

class SkladCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Sklad
    form_class = SkladCreateForm
    template_name = 'hpm_sklad/create_sklad.html'
    success_url = "/sklad/"
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
    template_name = 'hpm_sklad/audit_log.html'
    context_object_name = 'logs'
 
    
class SignUp(CreateView):
  form_class = CustomUserCreationForm
  success_url = reverse_lazy("login")
  template_name = "registration/signup.html"   
  
  
def logout_request(request):
  logout(request)
  return redirect("home")
