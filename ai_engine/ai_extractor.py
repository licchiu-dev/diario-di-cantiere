"""
ai_extractor.py – Modulo di estrazione attività strutturate dal diario di cantiere.

Struttura:
  extract_diary_activities(text, workers, environments, macro_tasks) -> list[dict]

Attualmente usa keyword matching (mock).
Per collegare OpenAI GPT in futuro, sostituire _extract_with_openai e
impostare USE_OPENAI=True nelle settings o come variabile d'ambiente.
"""
import re
from typing import Optional


# ── Mappa keyword → codice macrolavorazione ────────────────────────────────

KEYWORD_MAP = [
    # Cartongesso
    (['cartongesso', 'lastra', 'lastre', 'parete', 'pareti', 'divisoria'], 'CG01'),
    (['controsoffitto', 'soffitto', 'soffitta'], 'CG02'),
    (['veletta', 'gola led', 'gola luce', 'illuminazione indiretta'], 'CG03'),
    (['controparete', 'contropareti', 'rivestimento parete'], 'CG04'),
    # Finitura
    (['stuccatura q2', 'stucco q2', 'livello 2'], 'FN01'),
    (['stuccatura q3', 'stucco q3', 'rasatura q3', 'livello 3', 'stuccato'], 'FN02'),
    (['stuccatura q4', 'stucco q4', 'rasatura q4', 'livello 4', 'alta finitura'], 'FN03'),
    # Pittura
    (['fondo fissativo', 'fissativo', 'impregnante', 'primer'], 'PT01'),
    (['prima mano', 'prima mano pittura', '1 mano'], 'PT02'),
    (['seconda mano', 'seconda mano pittura', '2 mano', 'finitura pittura'], 'PT03'),
    (['pittura', 'tinteggiatura', 'verniciatura', 'dipinto', 'dipinta'], 'PT02'),
    # Protezioni
    (['masking', 'protezioni', 'nastro', 'telo protezione', 'protezione pavimento'], 'MS01'),
    # Resina
    (['resina', 'microcemento', 'microtopping', 'rivestimento resinoso'], 'RS01'),
    # Logistica
    (['preso dal deposito', 'ritirato dal deposito', 'materiale dal deposito',
      'portato in cantiere', 'scaricato', 'movimentazione materiali'], 'MT01'),
    # Extra e criticità
    (['manca', 'mancano', 'problema', 'problemi', 'fermo', 'fermi', 'ritardo',
      'ritardi', 'imprevisto', 'criticità', 'non preventivato', 'extra'], 'EX01'),
    (['nota tecnica', 'criticità', 'attenzione', 'da verificare', 'segnalazione',
      'problema strutturale', 'umidità', 'infiltrazione'], 'NT01'),
]


def _normalize(text: str) -> str:
    return text.lower().strip()


def _find_best_macrolavorazione(text: str, macro_tasks: list[dict]) -> Optional[dict]:
    """Cerca la macrolavorazione più pertinente tramite keyword matching."""
    text_norm = _normalize(text)
    best_code = None
    best_score = 0

    for keywords, code in KEYWORD_MAP:
        score = sum(1 for kw in keywords if kw in text_norm)
        if score > best_score:
            best_score = score
            best_code = code

    if best_code:
        for macro in macro_tasks:
            if macro.get('codice') == best_code:
                return macro
    return None


def _estimate_hours(text: str) -> Optional[float]:
    """Estrae ore stimate dal testo se presenti (es. '3 ore', '2.5h')."""
    patterns = [
        r'(\d+(?:[.,]\d+)?)\s*ore',
        r'(\d+(?:[.,]\d+)?)\s*h\b',
        r'(\d+(?:[.,]\d+)?)\s*giornate?',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            val = float(match.group(1).replace(',', '.'))
            if 'giornata' in match.group(0) or 'giornate' in match.group(0):
                val = val * 8  # converti in ore
            return val
    return None


def _assign_worker(text: str, workers: list[dict]) -> Optional[dict]:
    """Cerca un dipendente nominato nel testo."""
    text_norm = _normalize(text)
    for worker in workers:
        nome = _normalize(worker.get('nome', ''))
        cognome = _normalize(worker.get('cognome', ''))
        if nome and nome in text_norm:
            return worker
        if cognome and cognome in text_norm:
            return worker
    return None


def _assign_environment(text: str, environments: list[dict]) -> Optional[dict]:
    """Cerca un ambiente nominato nel testo."""
    text_norm = _normalize(text)
    for env in environments:
        nome = _normalize(env.get('nome', ''))
        if nome and nome in text_norm:
            return env
    return None


def _split_into_sentences(text: str) -> list[str]:
    """Divide il testo in frasi o paragrafi significativi."""
    # Suddivide per punto, punto e virgola, a capo
    parts = re.split(r'[.;\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _extract_mock(
    diary_text: str,
    workers: list[dict],
    environments: list[dict],
    macro_tasks: list[dict],
) -> list[dict]:
    """
    Estrazione mock basata su keyword matching.
    Ritorna una lista di attività strutturate.
    """
    results = []
    sentences = _split_into_sentences(diary_text)

    if not sentences:
        sentences = [diary_text]

    seen_codes = set()

    for sentence in sentences:
        macro = _find_best_macrolavorazione(sentence, macro_tasks)
        if not macro:
            continue

        code = macro.get('codice')
        # Evita duplicati esatti (stesso codice + stessa frase)
        key = f"{code}::{sentence[:40]}"
        if key in seen_codes:
            continue
        seen_codes.add(key)

        ore = _estimate_hours(sentence)
        worker = _assign_worker(sentence, workers)
        env = _assign_environment(sentence, environments)

        # Confidenza basata su numero di keyword trovate
        text_norm = _normalize(sentence)
        kw_hits = sum(
            1 for keywords, c in KEYWORD_MAP
            if c == code
            for kw in keywords
            if kw in text_norm
        )
        if kw_hits >= 2:
            confidenza = 'alta'
        elif kw_hits == 1:
            confidenza = 'media'
        else:
            confidenza = 'bassa'

        results.append({
            'dipendente_id': worker.get('id') if worker else None,
            'dipendente_nome': str(worker) if worker else None,
            'ambiente_id': env.get('id') if env else None,
            'ambiente_nome': env.get('nome') if env else None,
            'codice_macrolavorazione': code,
            'nome_macrolavorazione': macro.get('nome', ''),
            'macrolavorazione_id': macro.get('id'),
            'descrizione_attivita': sentence[:300],
            'ore_stimate': ore,
            'confidenza': confidenza,
            'note_ai': f'Rilevato tramite keyword matching. Frase analizzata: "{sentence[:80]}..."',
        })

    return results


# ── Punto di ingresso principale ───────────────────────────────────────────

def extract_diary_activities(
    diary_text: str,
    workers: list[dict],
    environments: list[dict],
    macro_tasks: list[dict],
) -> list[dict]:
    """
    Estrae attività strutturate dal testo libero di una giornata di cantiere.

    Args:
        diary_text:   Testo libero della giornata (descrizione + problemi/note).
        workers:      Lista di dict con chiavi 'id', 'nome', 'cognome'.
        environments: Lista di dict con chiavi 'id', 'nome'.
        macro_tasks:  Lista di dict con chiavi 'id', 'codice', 'nome'.

    Returns:
        Lista di dict con i campi dell'AttivitaDiario da creare.
    """
    if not diary_text or not diary_text.strip():
        return []

    # Qui in futuro si può aggiungere: if settings.USE_OPENAI: return _extract_with_openai(...)
    return _extract_mock(diary_text, workers, environments, macro_tasks)


# ── Stub per futura integrazione OpenAI ───────────────────────────────────

def _extract_with_openai(
    diary_text: str,
    workers: list[dict],
    environments: list[dict],
    macro_tasks: list[dict],
) -> list[dict]:
    """
    Integrazione futura con OpenAI GPT.
    Da implementare quando si vuole passare dal mock a una vera AI.

    Esempio di utilizzo:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        ...
    """
    raise NotImplementedError(
        "Integrazione OpenAI non ancora configurata. "
        "Impostare OPENAI_API_KEY nelle variabili d'ambiente e implementare questa funzione."
    )
