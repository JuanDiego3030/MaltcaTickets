from django.urls import path
from . import views
from .views import exportar_reporte_pdf

urlpatterns = [
        path('', views.login, name='login'),
        path('panel/control/', views.panel_control, name='panel_control'),
        path('logout/', views.logout, name='logout'),
    path('exportar-reporte-pdf/', exportar_reporte_pdf, name='exportar_reporte_pdf'),
    ]