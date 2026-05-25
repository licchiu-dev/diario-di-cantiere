"""
Estrazione cluster attività tramite OpenAI GPT-4o-mini.
Se la chiave API non è disponibile, le giornate vengono salvate senza cluster
e il testo grezzo rimane visibile nella pagina del cantiere.
"""
import json


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_prompt_categorie() -> str:
    try:
        from core.models import CategoriaLavorazione
        cats = CategoriaLavorazione.objects.all()
        if cats.exists():
            return "\n".join(f"- {c.key}: {c.nome}" for c in cats)
    except Exception:
        pass
    return "- altro: Altro"


def _get_or_create_ambiente(cantiere, nome: str):
    if not nome:
        return None
    from core.models import Ambiente
    nome = nome.strip().title()
    obj, _ = Ambiente.objects.get_or_create(
        cantiere=cantiere,
        nome__iexact=nome,
        defaults={'nome': nome},
    )
    return obj


# ── Estrazione OpenAI ─────────────────────────────────────────────────────────

def _extract_with_openai(testo: str, fonte: str, n_operai: int, ore_lavorate: float) -> list[dict] | None:
    try:
        from django.conf import settings
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return None

        from openai import OpenAI

        cat_str = _build_prompt_categorie()

        if fonte == 'materiali':
            istr_ore = "Stai analizzando bolle di materiale: ore_stimate deve essere sempre null."
        else:
            istr_ore = (
                f"Ci sono {n_operai} operai in cantiere per {ore_lavorate}h ciascuno.\n"
                "ore_stimate = ore-uomo TOTALI (n. persone × ore individuali).\n"
                "Esempi: 'Roberto e Leo, 5 ore' → 10.0 | 'Marco 3h' → 3.0 | senza ore → null"
            )

        system = f"""Sei un assistente per diari di cantiere italiani. Analizza il testo e suddividilo in attività separate.

Categorie disponibili:
{cat_str}

{istr_ore}

Per ogni attività estrai:
- categoria: chiave dalla lista sopra
- descrizione: testo pulito (senza ore e senza nomi di persone)
- ore_stimate: ore-uomo TOTALI. null se non specificato.
- dipendenti: lista nomi delle persone che svolgono questa attività ([] se non specificato)
- ambiente: locale o area dove si lavora (es. "Bagno padronale", "Piano -1"). null se non specificato.
- avanzamento: "iniziato", "in_corso" o "completato". null se non chiaro.

Rispondi SOLO con JSON:
{{"clusters": [{{"categoria":"...", "descrizione":"...", "ore_stimate":null, "dipendenti":[], "ambiente":null, "avanzamento":null}}]}}"""

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": testo},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1000,
        )

        data = json.loads(response.choices[0].message.content)
        clusters = data.get("clusters", [])

        return [
            {
                'fonte': fonte,
                'categoria': c.get('categoria', 'altro'),
                'descrizione': str(c.get('descrizione', '')).strip()[:400],
                'ore_stimate': float(c['ore_stimate']) if c.get('ore_stimate') is not None else None,
                'n_persone': 1,
                'dipendenti_nomi': ', '.join(c.get('dipendenti') or []),
                'ambiente_nome': str(c['ambiente']).strip() if c.get('ambiente') else '',
                'avanzamento': c.get('avanzamento') or '',
            }
            for c in clusters
            if str(c.get('descrizione', '')).strip()
        ]

    except Exception:
        return None


# ── Entry point ───────────────────────────────────────────────────────────────

def processa_giornata(giornata) -> None:
    from core.models import ClusterAttivita

    ore_uomo_totali = float(giornata.n_operai) * float(giornata.ore_lavorate)

    campi = [
        (giornata.desc_preventivo, 'preventivo'),
        (giornata.desc_extra,      'extra'),
        (giornata.desc_materiali,  'materiali'),
    ]

    tutti = []
    for testo, fonte in campi:
        if not testo.strip():
            continue
        clusters = _extract_with_openai(testo, fonte, giornata.n_operai, float(giornata.ore_lavorate))
        if clusters:
            tutti.extend(clusters)

    if not tutti:
        # Nessun cluster (API key mancante o testo vuoto): testo grezzo resta visibile
        giornata.ai_processata = True
        giornata.save(update_fields=['ai_processata'])
        return

    cluster_lavoro = [c for c in tutti if c.get('categoria') != 'materiali']
    cluster_mat    = [c for c in tutti if c.get('categoria') == 'materiali']

    # Distribuisci ore residue proporzionalmente ai cluster senza ore esplicite
    ore_esplicite = sum(c['ore_stimate'] for c in cluster_lavoro if c.get('ore_stimate') is not None)
    ore_residue   = max(0.0, ore_uomo_totali - ore_esplicite)

    senza_ore = [(i, c) for i, c in enumerate(cluster_lavoro) if c.get('ore_stimate') is None]
    pesi      = [c.get('n_persone', 1) for _, c in senza_ore]
    tot_peso  = sum(pesi) or 1

    for j, (i, _) in enumerate(senza_ore):
        cluster_lavoro[i]['ore_stimate'] = round(ore_residue * pesi[j] / tot_peso, 1)

    da_creare = [
        ClusterAttivita(
            giornata=giornata,
            fonte=c['fonte'],
            categoria=c['categoria'],
            descrizione=c['descrizione'][:400],
            ore_stimate=round(float(c['ore_stimate']), 1),
            ambiente=_get_or_create_ambiente(giornata.cantiere, c.get('ambiente_nome', '')),
            dipendenti_nomi=c.get('dipendenti_nomi', ''),
            avanzamento=c.get('avanzamento', ''),
        )
        for c in cluster_lavoro
    ] + [
        ClusterAttivita(
            giornata=giornata,
            fonte=c['fonte'],
            categoria=c['categoria'],
            descrizione=c['descrizione'][:400],
            ore_stimate=None,
            ambiente=_get_or_create_ambiente(giornata.cantiere, c.get('ambiente_nome', '')),
            dipendenti_nomi=c.get('dipendenti_nomi', ''),
            avanzamento=c.get('avanzamento', ''),
        )
        for c in cluster_mat
    ]

    ClusterAttivita.objects.bulk_create(da_creare)
    giornata.ai_processata = True
    giornata.save(update_fields=['ai_processata'])
