from django.contrib import admin
from .models import Dipendente, Cantiere, GiornataDiario, ClusterAttivita, RegolaKeyword


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


class ClusterInline(admin.TabularInline):
    model = ClusterAttivita
    extra = 0
    readonly_fields = ['fonte', 'categoria', 'descrizione', 'ore_stimate']


@admin.register(RegolaKeyword)
class RegolaKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'categoria']
    list_filter = ['categoria']
    search_fields = ['keyword']
    list_editable = ['categoria']


@admin.register(GiornataDiario)
class GiornataDiarioAdmin(admin.ModelAdmin):
    list_display = ['data', 'cantiere', 'n_operai', 'ore_lavorate', 'ai_processata']
    list_filter = ['cantiere', 'ai_processata']
    date_hierarchy = 'data'
    inlines = [ClusterInline]
