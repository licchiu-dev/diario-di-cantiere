from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from .models import Cantiere, GiornataDiario, ClusterAttivita
from .forms import GiornataDiarioForm, CantiereForm
from ai_engine.extractor import processa_giornata


# ── Cantieri ───────────────────────────────────────────────────────────────

@login_required
def cantieri_list(request):
    cantieri = Cantiere.objects.all()
    return render(request, 'cantieri_list.html', {'cantieri': cantieri})


@login_required
def cantiere_detail(request, pk):
    cantiere = get_object_or_404(Cantiere, pk=pk)
    giornate = (
        cantiere.giornate
        .prefetch_related('clusters')
        .order_by('-data')
    )

    # Statistiche ore-uomo
    ore_totali = sum(g.ore_uomo for g in giornate)
    n_giornate = giornate.count()

    # Ore per categoria con subtotali preventivo / extra
    qs_cat = (
        ClusterAttivita.objects
        .filter(giornata__cantiere=cantiere)
        .exclude(ore_stimate=None)
        .values('categoria')
        .annotate(
            ore_tot=Sum('ore_stimate'),
            ore_prev=Sum('ore_stimate', filter=Q(fonte='preventivo')),
            ore_extra=Sum('ore_stimate', filter=Q(fonte='extra')),
        )
        .order_by('-ore_tot')
    )

    cat_labels = dict(ClusterAttivita.CATEGORIA_CHOICES)
    categorie_cards = [
        {
            'key': r['categoria'],
            'nome': cat_labels.get(r['categoria'], r['categoria']),
            'ore_tot': float(r['ore_tot'] or 0),
            'ore_prev': float(r['ore_prev'] or 0),
            'ore_extra': float(r['ore_extra'] or 0),
        }
        for r in qs_cat
    ]

    # Totali globali preventivo vs extra per i KPI principali
    totali = (
        ClusterAttivita.objects
        .filter(giornata__cantiere=cantiere)
        .exclude(ore_stimate=None)
        .aggregate(
            ore_prev=Sum('ore_stimate', filter=Q(fonte='preventivo')),
            ore_extra=Sum('ore_stimate', filter=Q(fonte='extra')),
        )
    )

    return render(request, 'cantiere_detail.html', {
        'cantiere': cantiere,
        'giornate': giornate,
        'ore_totali': ore_totali,
        'n_giornate': n_giornate,
        'ore_prev_totali': float(totali['ore_prev'] or 0),
        'ore_extra_totali': float(totali['ore_extra'] or 0),
        'categorie_cards': categorie_cards,
    })


@login_required
def cantiere_create(request):
    if request.method == 'POST':
        form = CantiereForm(request.POST)
        if form.is_valid():
            cantiere = form.save()
            messages.success(request, f'Cantiere "{cantiere.nome}" creato.')
            return redirect('cantiere_detail', pk=cantiere.pk)
    else:
        form = CantiereForm()
    return render(request, 'cantiere_form.html', {'form': form, 'title': 'Nuovo cantiere'})


@login_required
def cantiere_update(request, pk):
    cantiere = get_object_or_404(Cantiere, pk=pk)
    if request.method == 'POST':
        form = CantiereForm(request.POST, instance=cantiere)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cantiere aggiornato.')
            return redirect('cantiere_detail', pk=cantiere.pk)
    else:
        form = CantiereForm(instance=cantiere)
    return render(request, 'cantiere_form.html', {
        'form': form,
        'cantiere': cantiere,
        'title': f'Modifica – {cantiere.nome}',
    })


# ── Giornate ───────────────────────────────────────────────────────────────

@login_required
def giornata_create(request):
    cantiere_pk = request.GET.get('cantiere')
    if request.method == 'POST':
        form = GiornataDiarioForm(request.POST)
        if form.is_valid():
            giornata = form.save()
            processa_giornata(giornata)
            messages.success(request, f'Giornata del {giornata.data.strftime("%d/%m/%Y")} salvata.')
            return redirect('cantiere_detail', pk=giornata.cantiere.pk)
    else:
        form = GiornataDiarioForm(cantiere_pk=cantiere_pk)
    return render(request, 'giornata_form.html', {
        'form': form,
        'title': 'Nuova giornata',
    })


@login_required
def giornata_update(request, pk):
    giornata = get_object_or_404(GiornataDiario, pk=pk)
    if request.method == 'POST':
        form = GiornataDiarioForm(request.POST, instance=giornata)
        if form.is_valid():
            giornata = form.save()
            # Rielabora i cluster AI
            giornata.clusters.all().delete()
            giornata.ai_processata = False
            giornata.save()
            processa_giornata(giornata)
            messages.success(request, 'Giornata aggiornata.')
            return redirect('cantiere_detail', pk=giornata.cantiere.pk)
    else:
        form = GiornataDiarioForm(instance=giornata)
    return render(request, 'giornata_form.html', {
        'form': form,
        'giornata': giornata,
        'title': f'Modifica – {giornata.data_label}',
    })


@login_required
def giornata_delete(request, pk):
    giornata = get_object_or_404(GiornataDiario, pk=pk)
    cantiere_pk = giornata.cantiere.pk
    if request.method == 'POST':
        giornata.delete()
        messages.success(request, 'Giornata eliminata.')
    return redirect('cantiere_detail', pk=cantiere_pk)
