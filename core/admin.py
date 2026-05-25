from django.contrib import admin
from .models import Dipendente, Cantiere, GiornataDiario, ClusterAttivita, CategoriaLavorazione, Ambiente


@admin.register(Dipendente)
class DipendenteAdmin(admin.ModelAdmin):
    list_display = ['cognome', 'nome', 'ruolo', 'costo_orario', 'attivo']
    list_filter = ['ruolo', 'attivo']
    search_fields = ['cognome', 'nome']
    list_editable = ['attivo']


@admin.register(Cantiere)
class CantiereAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cliente', 'stato', 'data_inizio']
    list_filter = ['stato']
    search_fields = ['nome', 'cliente']
    list_editable = ['stato']


@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cantiere']
    list_filter = ['cantiere']
    search_fields = ['nome']


class ClusterInline(admin.TabularInline):
    model = ClusterAttivita
    extra = 0
    readonly_fields = ['fonte', 'categoria', 'descrizione', 'ore_stimate', 'ambiente', 'dipendenti_nomi', 'avanzamento']


@admin.register(CategoriaLavorazione)
class CategoriaLavorazioneAdmin(admin.ModelAdmin):
    list_display = ['nome', 'key', 'tema', 'ordine']
    list_editable = ['tema', 'ordine']
    prepopulated_fields = {'key': ('nome',)}



@admin.register(GiornataDiario)
class GiornataDiarioAdmin(admin.ModelAdmin):
    list_display = ['data', 'cantiere', 'ai_processata']
    list_filter = ['cantiere', 'ai_processata']
    date_hierarchy = 'data'
    inlines = [ClusterInline]
