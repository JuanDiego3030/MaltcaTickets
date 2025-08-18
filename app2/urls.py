from django.urls import path
from . import views

urlpatterns = [
        path('crear_ticket/', views.crear_ticket, name='crear_ticket'),
    ]