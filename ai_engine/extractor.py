"""
Estrazione automatica cluster attività dal testo libero della giornata.

Logica: keyword matching per frase + stima persone per distribuzione ore proporzionale.
Pronto per sostituire con OpenAI: basta implementare _extract_con_openai()
e chiamarla invece di _extract_mock().
"""
import re

_STOP_WORDS = {
    'della', 'delle', 'dello', 'degli', 'nella', 'nelle', 'nello', 'negli',
    'sulla', 'sulle', 'sullo', 'alla', 'alle', 'agli', 'dalle', 'dallo',
    'con', 'per', 'che', 'una', 'uno', 'gli', 'lei', 'lui', 'sua', 'suo',
    'suoi', 'sue', 'come', 'dove', 'quando', 'hanno', 'sono', 'era', 'anche',
    'tutto', 'tutti', 'tutte', 'tutta', 'tra', 'fra', 'questo', 'questa',
    'questi', 'queste', 'stato', 'stati', 'stata', 'state', 'essere', 'avere',
    'fare', 'molto', 'bene', 'male', 'dopo', 'prima', 'ancora', 'sempre',
    'piano', 'parte', 'area', 'zona', 'lato', 'cont', 'lavoro', 'lavori',
}

# Mappa keyword → categoria macrolavorazione
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
        'rifacimento intonaco', 'ripristino intonaco', 'stabilitura',
        'arriccio', 'rinzaffo', 'spigoli', 'raccordo',
    ],
    'pittura': [
        'pittura', 'tinteggiatura', 'verniciatura', 'dipingere',
        'prima mano', 'seconda mano', '1 mano', '2 mano',
        'fissativo', 'fondo', 'impregnante', 'primer',
        'idropittura', 'quarzo',
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

# Marcatori che segnalano la fine del soggetto (chi fa l'azione)
_FINE_SOGGETTO = [
    ' si sono ', ' hanno ', ' ha ', ' si è ', ' sono ', ' è ',
    ' invece ', ' si ', ' dedica', ' lavora', ' fanno ', ' fa ',
]


def _conta_persone(frase: str) -> int:
    """
    Stima quante persone stanno lavorando sull'attività descritta nella frase,
    contando i connettori "e" e le virgole nella parte di soggetto.

    Es. "Marco e Leo si sono dedicati..."  → soggetto "Marco e Leo" → 2
        "Leo, Massimo e Giuseppe invece..." → soggetto "Leo, Massimo e Giuseppe" → 3
    """
    frase_l = frase.lower().strip()

    # Estrai la porzione di soggetto (prima del verbo/marcatore)
    soggetto = frase_l
    for marcatore in _FINE_SOGGETTO:
        if marcatore in frase_l:
            soggetto = frase_l[: frase_l.index(marcatore)]
            break

    # Limita a un ragionevole numero di token per non catturare il predicato
    soggetto = ' '.join(soggetto.split()[:12])

    n_e = soggetto.count(' e ')
    n_virgole = soggetto.count(',')
    return max(1, n_e + n_virgole + 1)


def _classifica(testo: str) -> str:
    """Restituisce la categoria più pertinente in base alle keyword."""
    testo_l = testo.lower()
    punteggi = {}

    # Regole apprese dall'utente: peso 3 (priorità sulle keyword di default)
    try:
        from core.models import RegolaKeyword
        for regola in RegolaKeyword.objects.all():
            if regola.keyword in testo_l:
                punteggi[regola.categoria] = punteggi.get(regola.categoria, 0) + 3
    except Exception:
        pass

    # Keyword di default: peso 1
    for cat, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in testo_l)
        if score > 0:
            punteggi[cat] = punteggi.get(cat, 0) + score

    if not punteggi:
        return 'altro'
    return max(punteggi, key=punteggi.get)


def apprendi_da_correzione(descrizione: str, categoria: str) -> None:
    """Salva le keyword significative della descrizione come regole apprese."""
    from core.models import RegolaKeyword
    words = re.findall(r'[a-zàèéìòù]+', descrizione.lower())
    keywords = [w for w in words if len(w) >= 5 and w not in _STOP_WORDS]
    for kw in keywords:
        RegolaKeyword.objects.update_or_create(keyword=kw, defaults={'categoria': categoria})


def _dividi_in_frasi(testo: str) -> list[str]:
    """Spezza il testo in frasi significative."""
    frasi = re.split(r'[.;\n]+', testo)
    return [f.strip() for f in frasi if len(f.strip()) > 12]


def _extract_mock(testo: str, fonte: str) -> list[dict]:
    """Estrazione mock via keyword matching."""
    if not testo.strip():
        return []

    if fonte == 'materiali':
        # Le bolle di materiale le raggruppiamo come categoria materiali
        frasi = _dividi_in_frasi(testo)
        if not frasi:
            frasi = [testo.strip()]
        return [
            {'fonte': fonte, 'categoria': CATEGORIA_MATERIALI, 'descrizione': f}
            for f in frasi
        ]

    frasi = _dividi_in_frasi(testo)
    if not frasi:
        frasi = [testo.strip()]

    risultati = []
    for frase in frasi:
        categoria = _classifica(frase)
        if fonte == 'extra' and categoria == 'altro':
            categoria = 'extra'
        risultati.append({
            'fonte': fonte,
            'categoria': categoria,
            'descrizione': frase,
            'n_persone': _conta_persone(frase),   # usato per la distribuzione proporzionale
        })
    return risultati


def processa_giornata(giornata) -> None:
    """
    Legge i tre campi testo della giornata, estrae cluster e li salva.
    Distribuisce le ore-uomo totali equamente tra i cluster trovati.
    """
    from core.models import ClusterAttivita

    ore_uomo_totali = float(giornata.n_operai) * float(giornata.ore_lavorate)

    campi = [
        (giornata.desc_preventivo, 'preventivo'),
        (giornata.desc_extra, 'extra'),
        (giornata.desc_materiali, 'materiali'),
    ]

    tutti_i_cluster = []
    for testo, fonte in campi:
        tutti_i_cluster.extend(_extract_mock(testo, fonte))

    if not tutti_i_cluster:
        giornata.ai_processata = True
        giornata.save(update_fields=['ai_processata'])
        return

    # Distribuzione proporzionale delle ore: i cluster materiali non ricevono ore lavoro
    cluster_lavoro = [c for c in tutti_i_cluster if c['categoria'] != CATEGORIA_MATERIALI]
    cluster_mat = [c for c in tutti_i_cluster if c['categoria'] == CATEGORIA_MATERIALI]

    # Peso = n. persone stimate per cluster; la somma deve coincidere con n_operai totali.
    # Se la somma stimata supera il totale, normalizziamo proporzionalmente.
    pesi = [c.get('n_persone', 1) for c in cluster_lavoro]
    tot_peso = sum(pesi) or 1

    da_creare = []
    for c, peso in zip(cluster_lavoro, pesi):
        ore_cluster = round(ore_uomo_totali * peso / tot_peso, 1)
        da_creare.append(ClusterAttivita(
            giornata=giornata,
            fonte=c['fonte'],
            categoria=c['categoria'],
            descrizione=c['descrizione'][:400],
            ore_stimate=ore_cluster,
        ))
    for c in cluster_mat:
        da_creare.append(ClusterAttivita(
            giornata=giornata,
            fonte=c['fonte'],
            categoria=c['categoria'],
            descrizione=c['descrizione'][:400],
            ore_stimate=None,
        ))

    ClusterAttivita.objects.bulk_create(da_creare)

    giornata.ai_processata = True
    giornata.save(update_fields=['ai_processata'])
