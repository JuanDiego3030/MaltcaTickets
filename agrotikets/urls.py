from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('app1.urls')),
    path('tickets/', include('app2.urls')),
    path('bot/', include('app3.urls')),
]