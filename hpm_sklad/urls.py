from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sklad/', views.SkladListView.as_view(), name='sklad'),
    path('sklad/new/', views.SkladCreateView.as_view(), name='create_sklad'),
    path('sklad/<int:pk>/detail/', views.SkladDetailView.as_view(), name='detail_sklad'),
    path('sklad/<int:pk>/update/', views.SkladUpdateView.as_view(), name='update_sklad'),
    path('sklad/<int:pk>/update_objednano/', views.SkladUpdateObjednanoView.as_view(), name='update_objednano_sklad'),
    path('sklad/<int:pk>/delete/', views.SkladDeleteView.as_view(), name='delete_sklad'),
    path('sklad/audit_logs/', views.AuditLogListView.as_view(), name='audit_log'),
    path('sklad/<int:pk>/create_audit_log/', views.receipt_form_view, name='create_audit_log'),
    path('account/', include('django.contrib.auth.urls')),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("logout/", views.logout_request, name= "logout")
]
