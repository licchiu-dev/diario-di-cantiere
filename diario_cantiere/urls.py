from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.cantieri_list, name='cantieri_list'),
    path('cantieri/<int:pk>/', views.cantiere_detail, name='cantiere_detail'),
    path('giornata/nuova/', views.giornata_create, name='giornata_create'),
    path('giornata/<int:pk>/modifica/', views.giornata_update, name='giornata_update'),
    path('giornata/<int:pk>/elimina/', views.giornata_delete, name='giornata_delete'),
    path('giornata/<int:pk>/rielabora/', views.giornata_rielabora, name='giornata_rielabora'),
    path('cantieri/nuovo/', views.cantiere_create, name='cantiere_create'),
    path('cantieri/<int:pk>/modifica/', views.cantiere_update, name='cantiere_update'),
    path('cluster/<int:pk>/modifica/', views.cluster_update, name='cluster_update'),
    path('backup/', views.esporta_backup, name='esporta_backup'),
    path('health/', views.health, name='health'),
]
