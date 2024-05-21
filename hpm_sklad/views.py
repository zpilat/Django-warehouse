from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Sklad, AuditLog
from .forms import SkladCreateForm, SkladUpdateForm, SkladUpdateObjednanoForm, AuditLogCreateForm, CustomUserCreationForm

def home_view(request):
    return render(request, "hpm_sklad/home.html")

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

class SkladCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Sklad
    form_class = SkladCreateForm
    template_name = 'hpm_sklad/create_sklad.html'
    success_url = "/sklad/"
    permission_required = 'hpm_sklad.create_sparepart'

class SkladUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateForm    
    template_name = 'hpm_sklad/update_sklad.html'
    success_url = "/sklad/"
    permission_required = 'hpm_sklad.update_sparepart'
    
class SkladUpdateObjednanoView(LoginRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladUpdateObjednanoForm    
    template_name = 'hpm_sklad/update_objednano_sklad.html'
    success_url = "/sklad/"

class SkladDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Sklad
    template_name = 'hpm_sklad/delete_sklad.html'
    success_url = "/sklad/"
    permission_required = 'hpm_sklad.delete_sparepart'
    

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
    
class AuditLogCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Sklad
    form_class = AuditLogCreateForm    
    template_name = 'hpm_sklad/create_audit_log.html'
    success_url = reverse_lazy("audit_log")
    permission_required = 'hpm_sklad.create_sparepart'    
    
class SignUp(CreateView):
  form_class = CustomUserCreationForm
  success_url = reverse_lazy("login")
  template_name = "registration/signup.html"    
  
def logout_request(request):
  logout(request)
  return redirect("home")
