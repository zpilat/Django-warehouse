from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sklad/', views.SkladListView.as_view(), name='sklad'),
    path('sklad/export/csv/', views.SkladListView.as_view(export_csv=True), name='sklad_export_csv'),
    path('sklad/new/', views.SkladCreateView.as_view(), name='create_sklad'),
    path('sklad/<int:pk>/detail/', views.SkladDetailView.as_view(), name='detail_sklad'),
    path('sklad/<int:pk>/update/', views.SkladUpdateView.as_view(), name='update_sklad'),
    path('sklad/<int:pk>/update_objednano/', views.SkladUpdateObjednanoView.as_view(), name='update_objednano_sklad'),
    path('sklad/<int:pk>/delete/', views.SkladDeleteView.as_view(), name='delete_sklad'),
    path('sklad/audit_logs/', views.AuditLogListView.as_view(), name='audit_log'),
    path('sklad/audit_logs/export/csv/', views.AuditLogListView.as_view(export_csv=True), name='audit_log_export_csv'),
    path('sklad/audit_logs/graph/', views.AuditLogListView.as_view(graph=True), name='audit_log_graph'),    
    path('sklad/audit_logs/<int:pk>/detail/', views.AuditLogDetailView.as_view(), name='detail_audit_log'),
    path('sklad/<int:pk>/create_varianty/', views.VariantyCreateView.as_view(), name='create_varianty'),
    path('sklad/<int:pk>/update_varianty/', views.VariantyUpdateView.as_view(), name='update_varianty'),
    path('sklad/<int:pk>/create_varianty_with_dodavatel/<int:dodavatel>/', views.VariantyWithDodavatelCreateView.as_view(), name='create_varianty_with_dodavatel'),
    path('sklad/<int:pk>/receipt_audit_log/', views.receipt_form_view, name='receipt_audit_log'),
    path('sklad/<int:pk>/dispatch_audit_log/', views.dispatch_form_view, name='dispatch_audit_log'),
    path('sklad/dodavatele/', views.DodavateleListView.as_view(), name='dodavatele'),
    path('sklad/dodavatele/<int:pk>/detail/', views.DodavateleDetailView.as_view(), name='detail_dodavatele'),    
    path('sklad/dodavatele/export/', views.DodavateleListView.as_view(export_csv=True), name='dodavatele_export_csv'),    
    path('account/', include('django.contrib.auth.urls')),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("logout/", views.logout_request, name= "logout")
]
