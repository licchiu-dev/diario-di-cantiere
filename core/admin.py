from django.contrib import admin
from django import forms as django_forms
from .models import Dipendente, Cantiere, GiornataDiario, ClusterAttivita, RegolaKeyword, CategoriaLavorazione


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


@admin.register(CategoriaLavorazione)
class CategoriaLavorazioneAdmin(admin.ModelAdmin):
    list_display = ['nome', 'key', 'tema', 'ordine']
    list_editable = ['tema', 'ordine']
    prepopulated_fields = {'key': ('nome',)}


@admin.register(RegolaKeyword)
class RegolaKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'categoria']
    list_filter = ['categoria']
    search_fields = ['keyword']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        scelte = [('', '---------')] + [
            (c.key, c.nome) for c in CategoriaLavorazione.objects.all()
        ]
        form.base_fields['categoria'].widget = django_forms.Select(choices=scelte)
        return form


@admin.register(GiornataDiario)
class GiornataDiarioAdmin(admin.ModelAdmin):
    list_display = ['data', 'cantiere', 'n_operai', 'ore_lavorate', 'ai_processata']
    list_filter = ['cantiere', 'ai_processata']
    date_hierarchy = 'data'
    inlines = [ClusterInline]
