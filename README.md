# Diario di Cantiere

Gestionale operativo per imprese edili. Permette di registrare ogni giornata di lavoro: chi era in cantiere, cosa è stato fatto, quali materiali sono stati usati, e analizzare i dati con un motore AI (mock + predisposto per OpenAI).

---

## Stack tecnologico

| Layer | Tecnologia |
|---|---|
| Backend | Django 4.2 |
| Database | SQLite (sviluppo) / PostgreSQL (produzione) |
| Frontend | Django Templates + Bootstrap 5 |
| AI | Mock keyword-matching → predisposto OpenAI GPT |
| Static files | Whitenoise |
| Deploy | Railway / Render / PythonAnywhere |

---

## Installazione in locale

### 1. Clona o copia il progetto

```bash
cd "diario di cantiere"
```

### 2. Crea il virtualenv e installa le dipendenze

```bash
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

### 3. Crea il file .env

```bash
cp .env.example .env
# Modifica SECRET_KEY con una stringa casuale sicura
```

### 4. Esegui le migrazioni

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crea il superuser per l'admin

```bash
python manage.py createsuperuser
```

### 6. Popola i dati iniziali (macrolavorazioni, dipendenti demo, deposito)

```bash
python manage.py seed_data
```

### 7. Avvia il server di sviluppo

```bash
python manage.py runserver
```

Apri il browser su: **http://127.0.0.1:8000**

---

## Struttura del progetto

```
diario_cantiere/        → configurazione Django (settings, urls, wsgi)
core/                   → dashboard, comando seed_data
anagrafiche/            → Dipendenti, Fornitori, Depositi, Macrolavorazioni, Materiali
cantieri/               → Cantieri, Ambienti
diario/                 → GiornataDiario, Presenze, AttivitaDiario, MovimentiMateriali, Foto
reports/                → Report cantiere, Report macrolavorazione, Consuntivo
ai_engine/              → ai_extractor.py (mock AI + stub OpenAI)
templates/              → Tutti i template HTML (Bootstrap 5)
static/                 → CSS custom + JS
```

---

## Workflow operativo consigliato

1. **Crea i cantieri** in Anagrafiche → Cantieri
2. **Aggiungi ambienti** al cantiere (salotto, cucina, corridoio, ecc.)
3. **Registra dipendenti** in Anagrafiche → Dipendenti con costo orario
4. **Ogni giorno di lavoro**: clicca "Nuova giornata"
   - Seleziona cantiere e data
   - Inserisci gli operai presenti con le ore lavorate
   - Seleziona gli ambienti interessati
   - Scrivi liberamente la descrizione delle lavorazioni
   - Aggiungi i materiali usati/acquistati
   - Annota eventuali problemi
   - Salva
5. **Analizza con AI**: nel dettaglio della giornata, clicca "Analizza con AI"
   - Il sistema legge la descrizione e crea attività strutturate
   - Revisiona le attività proposte
   - Conferma quelle corrette, modifica o elimina le errate
6. **Report**: consulta i report per cantiere, per macrolavorazione, e il consuntivo

---

## Come funziona il mock AI

Il file `ai_engine/ai_extractor.py` contiene la funzione principale:

```python
extract_diary_activities(diary_text, workers, environments, macro_tasks)
```

**Input:**
- `diary_text`: testo libero (descrizione lavorazioni + note)
- `workers`: lista operai presenti
- `environments`: lista ambienti del cantiere
- `macro_tasks`: lista macrolavorazioni disponibili

**Algoritmo mock:**
1. Divide il testo in frasi (per punto, punto e virgola, a capo)
2. Per ogni frase cerca corrispondenze con le keyword definite in `KEYWORD_MAP`
3. Stima le ore se trova pattern tipo "3 ore", "2.5h", "1 giornata"
4. Cerca nomi di operai e ambienti nel testo
5. Calcola un livello di confidenza (alta/media/bassa) in base alle keyword trovate

**Esempi di classificazione:**
- "cartongesso", "lastre", "pareti" → CG01 Pareti in cartongesso
- "controsoffitto", "soffitto" → CG02 Controsoffitti
- "veletta", "gola led" → CG03 Velette / Gole LED
- "stucco Q3", "rasatura" → FN02 Stuccatura Q3
- "pittura", "prima mano" → PT02 Prima mano pittura
- "preso dal deposito" → MT01 Movimentazione materiali
- "problema", "fermo", "manca" → NT01 Nota tecnica / Criticità

---

## Come collegare OpenAI GPT in futuro

### 1. Installa il client

```bash
pip install openai
```

### 2. Aggiungi la chiave API al .env

```env
OPENAI_API_KEY=sk-...
```

### 3. Implementa `_extract_with_openai` in `ai_engine/ai_extractor.py`

```python
from openai import OpenAI
from django.conf import settings

def _extract_with_openai(diary_text, workers, environments, macro_tasks):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = """Sei un assistente per imprese edili. Analizza il testo di una giornata
    di cantiere e restituisci un JSON con le attività rilevate..."""

    user_message = f"""
    Testo giornata: {diary_text}
    Operai: {workers}
    Ambienti: {environments}
    Macrolavorazioni: {macro_tasks}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)['attivita']
```

### 4. Abilita OpenAI in `extract_diary_activities`

```python
def extract_diary_activities(...):
    if getattr(settings, 'OPENAI_API_KEY', None):
        return _extract_with_openai(...)
    return _extract_mock(...)
```

---

## Deploy in produzione

### Opzione A: Railway (consigliato, gratuito per piccoli progetti)

1. Crea account su [railway.app](https://railway.app)
2. Crea nuovo progetto → "Deploy from GitHub repo"
3. Aggiungi servizio PostgreSQL
4. Imposta variabili d'ambiente:
   ```
   SECRET_KEY=chiave-segreta-lunga
   DEBUG=False
   ALLOWED_HOSTS=tuoapp.railway.app
   DATABASE_URL=<copiato da Railway>
   ```
5. Aggiungi `Procfile`:
   ```
   web: gunicorn diario_cantiere.wsgi --log-file -
   ```
6. Aggiungi `runtime.txt`:
   ```
   python-3.11.x
   ```
7. In `settings.py` decommentare il blocco `dj_database_url` e aggiungere:
   ```bash
   pip install dj-database-url
   ```

### Opzione B: Render

1. Crea account su [render.com](https://render.com)
2. Nuovo Web Service → connetti il repository GitHub
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start command: `gunicorn diario_cantiere.wsgi`
5. Aggiungi PostgreSQL come servizio separato

### Opzione C: PythonAnywhere (più semplice)

1. Crea account su [pythonanywhere.com](https://www.pythonanywhere.com)
2. Carica il progetto via Git o ZIP
3. Crea virtualenv e installa dipendenze
4. Configura WSGI file puntando a `diario_cantiere.wsgi`
5. Usa il database SQLite incluso (va bene per uso personale)

### Nota su Vercel

Vercel è ottimizzato per applicazioni Node.js e frontend statici. **Non è la scelta ideale per Django** in quanto:
- Non supporta nativamente Python WSGI
- Non ha storage persistente per SQLite
- Per farlo funzionare si dovrebbe usare Vercel + database esterno (Supabase, PlanetScale)

Consiglio: **Railway o Render** per Django + PostgreSQL. Sono più semplici e gratuiti per progetti piccoli.

---

## Comandi utili

```bash
# Avvia in sviluppo
python manage.py runserver

# Crea superuser
python manage.py createsuperuser

# Popola dati iniziali
python manage.py seed_data

# Crea migrazioni dopo modifica modelli
python manage.py makemigrations
python manage.py migrate

# Raccolta file statici per produzione
python manage.py collectstatic

# Shell Django
python manage.py shell
```

---

## Admin Django

Tutti i modelli sono registrati nell'admin Django.
Accedi su: **http://127.0.0.1:8000/admin/**

Funzionalità admin:
- GiornataDiario: visualizzazione con presenze e attività inline
- Cantieri: con ambienti inline
- Dipendenti: modifica rapida stato attivo
- Macrolavorazioni: ordinamento per codice, filtro per categoria
