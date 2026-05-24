from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.cantieri_list, name='cantieri_list'),
    path('cantieri/<int:pk>/', views.cantiere_detail, name='cantiere_detail'),
    path('giornata/nuova/', views.giornata_create, name='giornata_create'),
    path('giornata/<int:pk>/modifica/', views.giornata_update, name='giornata_update'),
    path('giornata/<int:pk>/elimina/', views.giornata_delete, name='giornata_delete'),
    path('cantieri/nuovo/', views.cantiere_create, name='cantiere_create'),
    path('cantieri/<int:pk>/modifica/', views.cantiere_update, name='cantiere_update'),
]
