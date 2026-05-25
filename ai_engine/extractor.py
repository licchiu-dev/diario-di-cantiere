"""
Estrazione cluster attività dal testo libero della giornata.

Priorità:
1. OpenAI GPT-4o-mini  (se OPENAI_API_KEY è impostata)
2. Keyword matching mock  (fallback locale, zero costi)
"""
import re
import json

# ── Keyword map (fallback se OpenAI non disponibile) ─────────────────────────

KEYWORD_MAP = {
    'cartongesso': [
        'cartongesso', 'lastra', 'lastre', 'gkb', 'gkf', 'parete cg',
        'pareti cg', 'divisoria', 'divisorie', 'controparete', 'contropareti',
        'controsoffitto', 'veletta', 'gola led', 'gola luce', 'profilo',
        'montante', 'traverso', 'struttura metallica',
    ],
    'finitura': [
        'stucco', 'stuccatura', 'stuccare', 'rasatura', 'rasare',
        'q2', 'q3', 'q4', 'livello 2', 'livello 3', 'livello 4',
        'giunti', 'nastro', 'rinforzo angoli', 'angolari', 'finitura',
        'lisciatura', 'intonaco', 'intonaci', 'intonacare', 'intonacatura',
        'stabilitura', 'arriccio', 'rinzaffo',
    ],
    'pittura': [
        'pittura', 'tinteggiatura', 'verniciatura', 'dipingere',
        'prima mano', 'seconda mano', '1 mano', '2 mano',
        'fissativo', 'fondo', 'impregnante', 'primer', 'idropittura', 'quarzo',
    ],
    'resina': [
        'resina', 'microcemento', 'microtopping', 'pavimento resinoso',
        'rivestimento resinoso', 'primer epossidico',
    ],
    'logistica': [
        'deposito', 'scarico', 'carico', 'trasporto', 'movimentazione',
        'portato in cantiere', 'sposta', 'spostamento materiali',
        'pulizia', 'riordino', 'sgombero',
    ],
    'extra': [
        'extra', 'imprevisto', 'non previsto', 'non preventivato',
        'problema', 'fermo', 'fermi', 'attesa', 'ritardo',
        'manca', 'mancano', 'bloccato', 'infiltrazione', 'umidità',
        'crack', 'crepa', 'difetto', 'correzione',
    ],
}

CATEGORIA_MATERIALI = 'materiali'

_STOP_WORDS = {
    'della', 'delle', 'dello', 'degli', 'nella', 'nelle', 'nello', 'negli',
    'sulla', 'sulle', 'sullo', 'alla', 'alle', 'agli', 'dalle', 'dallo',
    'con', 'per', 'che', 'una', 'uno', 'gli', 'lei', 'lui', 'sua', 'suo',
    'suoi', 'sue', 'come', 'dove', 'quando', 'hanno', 'sono', 'era', 'anche',
    'tutto', 'tutti', 'tutte', 'tutta', 'tra', 'fra', 'questo', 'questa',
    'questi', 'queste', 'stato', 'stati', 'stata', 'state', 'essere', 'avere',
    'fare', 'molto', 'bene', 'male', 'dopo', 'prima', 'ancora', 'sempre',
    'piano', 'parte', 'area', 'zona', 'lato', 'lavoro', 'lavori',
}

_FINE_SOGGETTO = [
    ' si sono ', ' hanno ', ' ha ', ' si è ', ' sono ', ' è ',
    ' invece ', ' si ', ' dedica', ' lavora', ' fanno ', ' fa ',
]


# ── Helper condivisi ──────────────────────────────────────────────────────────

def _conta_persone(frase: str) -> int:
    frase_l = frase.lower().strip()
    soggetto = frase_l
    for marcatore in _FINE_SOGGETTO:
        if marcatore in frase_l:
            soggetto = frase_l[: frase_l.index(marcatore)]
            break
    soggetto = ' '.join(soggetto.split()[:12])
    return max(1, soggetto.count(' e ') + soggetto.count(',') + 1)


def _estrai_ore(frase: str):
    """Estrae ore esplicite: '3 ore', '2h', '3.5h', '2,5 ore'."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:h\b|ore?\b)', frase.lower())
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


def _classifica(testo: str) -> str:
    testo_l = testo.lower()
    punteggi = {}

    # Regole apprese dall'utente (peso 3)
    try:
        from core.models import RegolaKeyword
        for r in RegolaKeyword.objects.all():
            if r.keyword in testo_l:
                punteggi[r.categoria] = punteggi.get(r.categoria, 0) + 3
    except Exception:
        pass

    # Keywords DB categorie (peso 2)
    try:
        from core.models import CategoriaLavorazione
        for cat in CategoriaLavorazione.objects.exclude(keywords=''):
            for kw in cat.keywords.splitlines():
                kw = kw.strip().lower()
                if kw and kw in testo_l:
                    punteggi[cat.key] = punteggi.get(cat.key, 0) + 2
    except Exception:
        pass

    # Keyword map hardcoded (peso 1)
    for cat, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in testo_l)
        if score:
            punteggi[cat] = punteggi.get(cat, 0) + score

    return max(punteggi, key=punteggi.get) if punteggi else 'altro'


def _dividi_in_frasi(testo: str) -> list[str]:
    frasi = re.split(r'[.;\n]+', testo)
    return [f.strip() for f in frasi if len(f.strip()) > 12]


# ── Estrazione mock (fallback) ────────────────────────────────────────────────

def _extract_mock(testo: str, fonte: str) -> list[dict]:
    if not testo.strip():
        return []

    if fonte == 'materiali':
        frasi = _dividi_in_frasi(testo) or [testo.strip()]
        return [{'fonte': fonte, 'categoria': CATEGORIA_MATERIALI, 'descrizione': f,
                 'ore_stimate': None} for f in frasi]

    frasi = _dividi_in_frasi(testo) or [testo.strip()]
    risultati = []
    for frase in frasi:
        categoria = _classifica(frase)
        if fonte == 'extra' and categoria == 'altro':
            categoria = 'extra'
        ore_esp = _estrai_ore(frase)
        n = _conta_persone(frase)
        risultati.append({
            'fonte': fonte,
            'categoria': categoria,
            'descrizione': frase,
            'ore_stimate': round(ore_esp * n, 1) if ore_esp is not None else None,
            'n_persone': n,
        })
    return risultati


# ── Estrazione OpenAI ─────────────────────────────────────────────────────────

def _build_prompt_categorie() -> str:
    try:
        from core.models import CategoriaLavorazione
        cats = CategoriaLavorazione.objects.all()
        if cats.exists():
            return "\n".join(f"- {c.key}: {c.nome}" for c in cats)
    except Exception:
        pass
    return "\n".join(f"- {k}" for k in list(KEYWORD_MAP.keys()) + ['materiali', 'altro'])


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
                "ore_stimate = ore-uomo TOTALI (persone × ore individuali).\n"
                "Esempi: 'Roberto e Leo, 5 ore' → 10.0 | 'Marco 3h' → 3.0 | attività senza ore → null"
            )

        system = f"""Sei un assistente per diari di cantiere italiani. Analizza il testo e suddividilo in attività separate.

Categorie disponibili:
{cat_str}

{istr_ore}

Rispondi SOLO con JSON nel formato:
{{"clusters": [{{"categoria": "chiave", "descrizione": "testo pulito senza ore", "ore_stimate": null}}]}}"""

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
            }
            for c in clusters
            if str(c.get('descrizione', '')).strip()
        ]

    except Exception:
        return None


# ── Apprendimento da correzioni ───────────────────────────────────────────────

def apprendi_da_correzione(descrizione: str, categoria: str) -> None:
    from core.models import RegolaKeyword
    words = re.findall(r'[a-zàèéìòù]+', descrizione.lower())
    for kw in words:
        if len(kw) >= 5 and kw not in _STOP_WORDS:
            RegolaKeyword.objects.update_or_create(keyword=kw, defaults={'categoria': categoria})


# ── Entry point principale ────────────────────────────────────────────────────

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
        if clusters is None:
            clusters = _extract_mock(testo, fonte)
        tutti.extend(clusters)

    if not tutti:
        giornata.ai_processata = True
        giornata.save(update_fields=['ai_processata'])
        return

    cluster_lavoro = [c for c in tutti if c.get('categoria') != CATEGORIA_MATERIALI]
    cluster_mat    = [c for c in tutti if c.get('categoria') == CATEGORIA_MATERIALI]

    # Ore residue da distribuire proporzionalmente
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
        )
        for c in cluster_lavoro
    ] + [
        ClusterAttivita(
            giornata=giornata,
            fonte=c['fonte'],
            categoria=c['categoria'],
            descrizione=c['descrizione'][:400],
            ore_stimate=None,
        )
        for c in cluster_mat
    ]

    ClusterAttivita.objects.bulk_create(da_creare)
    giornata.ai_processata = True
    giornata.save(update_fields=['ai_processata'])
