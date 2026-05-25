from django.db import models
from django.urls import reverse

TEMA_COLORI = {
    'blu':     {'sfondo': '#f0f9ff', 'testo': '#0c4a6e', 'bordo': '#bae6fd', 'badge_bg': '#e0f2fe', 'badge_txt': '#075985'},
    'verde':   {'sfondo': '#f0fdf4', 'testo': '#14532d', 'bordo': '#bbf7d0', 'badge_bg': '#dcfce7', 'badge_txt': '#15803d'},
    'giallo':  {'sfondo': '#fffbeb', 'testo': '#78350f', 'bordo': '#fde68a', 'badge_bg': '#fef3c7', 'badge_txt': '#92400e'},
    'viola':   {'sfondo': '#fdf4ff', 'testo': '#581c87', 'bordo': '#e9d5ff', 'badge_bg': '#f3e8ff', 'badge_txt': '#6b21a8'},
    'rosso':   {'sfondo': '#fff1f2', 'testo': '#881337', 'bordo': '#fecdd3', 'badge_bg': '#ffe4e6', 'badge_txt': '#9f1239'},
    'arancio': {'sfondo': '#fff7ed', 'testo': '#7c2d12', 'bordo': '#fed7aa', 'badge_bg': '#ffedd5', 'badge_txt': '#9a3412'},
    'grigio':  {'sfondo': '#f8fafc', 'testo': '#334155', 'bordo': '#e2e8f0', 'badge_bg': '#f1f5f9', 'badge_txt': '#475569'},
    'teal':    {'sfondo': '#f0fdfa', 'testo': '#134e4a', 'bordo': '#99f6e4', 'badge_bg': '#ccfbf1', 'badge_txt': '#0f766e'},
    'rosa':    {'sfondo': '#fdf2f8', 'testo': '#831843', 'bordo': '#f9a8d4', 'badge_bg': '#fce7f3', 'badge_txt': '#9d174d'},
}

_COLORI_DEFAULT = TEMA_COLORI['grigio']


class CategoriaLavorazione(models.Model):
    TEMA_CHOICES = [(k, k.title()) for k in TEMA_COLORI]

    key = models.SlugField(max_length=50, unique=True, help_text='Identificatore breve senza spazi (es. posa-pavimenti)')
    nome = models.CharField(max_length=100)
    tema = models.CharField(max_length=20, choices=TEMA_CHOICES, default='grigio')
    keywords = models.TextField(
        blank=True,
        help_text='Una keyword per riga. Usata per classificare automaticamente le attività.'
    )
    ordine = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']
        verbose_name = 'Categoria lavorazione'
        verbose_name_plural = 'Categorie lavorazioni'

    def __str__(self):
        return self.nome

    @property
    def colori(self):
        return TEMA_COLORI.get(self.tema, _COLORI_DEFAULT)


class Dipendente(models.Model):
    RUOLO_CHOICES = [
        ('operaio', 'Operaio'),
        ('caposquadra', 'Caposquadra'),
        ('tecnico', 'Tecnico'),
        ('subappaltatore', 'Subappaltatore'),
    ]
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    ruolo = models.CharField(max_length=50, choices=RUOLO_CHOICES, default='operaio')
    costo_orario = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='Costo orario (€/h)'
    )
    attivo = models.BooleanField(default=True)

    class Meta:
        ordering = ['cognome', 'nome']
        verbose_name = 'Dipendente'
        verbose_name_plural = 'Dipendenti'

    def __str__(self):
        return f"{self.cognome} {self.nome}"


class Cantiere(models.Model):
    STATO_CHOICES = [
        ('attivo', 'Attivo'),
        ('sospeso', 'Sospeso'),
        ('concluso', 'Concluso'),
    ]
    nome = models.CharField(max_length=200)
    cliente = models.CharField(max_length=200, blank=True)
    indirizzo = models.CharField(max_length=300, blank=True)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='attivo')
    data_inizio = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Cantiere'
        verbose_name_plural = 'Cantieri'

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('cantiere_detail', kwargs={'pk': self.pk})

    @property
    def ore_uomo_totali(self):
        result = self.giornate.aggregate(
            tot=models.Sum(
                models.F('n_operai') * models.F('ore_lavorate'),
                output_field=models.DecimalField()
            )
        )
        return result['tot'] or 0


class GiornataDiario(models.Model):
    data = models.DateField()
    cantiere = models.ForeignKey(Cantiere, on_delete=models.CASCADE, related_name='giornate')
    n_operai = models.PositiveSmallIntegerField(default=1, verbose_name='N. operai presenti')
    ore_lavorate = models.DecimalField(
        max_digits=4, decimal_places=1, default=8.0,
        verbose_name='Ore lavorate (per operaio)'
    )
    desc_preventivo = models.TextField(
        blank=True,
        verbose_name='Attività di preventivo',
        help_text='Descrivi liberamente le lavorazioni eseguite previste dal preventivo.'
    )
    desc_extra = models.TextField(
        blank=True,
        verbose_name='Attività extra',
        help_text='Descrivi le attività extra non previste dal preventivo.'
    )
    desc_materiali = models.TextField(
        blank=True,
        verbose_name='Bolle materiale',
        help_text='Descrivi i materiali ricevuti, ritirati o utilizzati oggi.'
    )
    ai_processata = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-created_at']
        verbose_name = 'Giornata'
        verbose_name_plural = 'Giornate'

    def __str__(self):
        return f"{self.cantiere.nome} – {self.data.strftime('%d/%m/%Y')}"

    def get_absolute_url(self):
        return reverse('cantiere_detail', kwargs={'pk': self.cantiere.pk})

    @property
    def ore_uomo(self):
        return self.n_operai * float(self.ore_lavorate)

    @property
    def data_label(self):
        GIORNI = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        MESI = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
        g = GIORNI[self.data.weekday()]
        m = MESI[self.data.month]
        return f"{g} {self.data.day} {m} {self.data.year}"


class Ambiente(models.Model):
    cantiere = models.ForeignKey(Cantiere, on_delete=models.CASCADE, related_name='ambienti')
    nome = models.CharField(max_length=150)

    class Meta:
        unique_together = [('cantiere', 'nome')]
        ordering = ['nome']
        verbose_name = 'Ambiente'
        verbose_name_plural = 'Ambienti'

    def __str__(self):
        return f"{self.cantiere.nome} – {self.nome}"


class ClusterAttivita(models.Model):
    FONTE_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('extra', 'Extra'),
        ('materiali', 'Materiali'),
    ]
    AVANZAMENTO_CHOICES = [
        ('iniziato',   'Iniziato'),
        ('in_corso',   'In corso'),
        ('completato', 'Completato'),
    ]
    giornata = models.ForeignKey(
        GiornataDiario, on_delete=models.CASCADE, related_name='clusters'
    )
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES)
    categoria = models.CharField(max_length=50, default='altro')
    descrizione = models.TextField()
    ore_stimate = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    ambiente = models.ForeignKey(
        Ambiente, null=True, blank=True, on_delete=models.SET_NULL, related_name='clusters'
    )
    dipendenti_nomi = models.CharField(max_length=300, blank=True)
    avanzamento = models.CharField(max_length=20, choices=AVANZAMENTO_CHOICES, blank=True)

    class Meta:
        ordering = ['categoria']
        verbose_name = 'Cluster attività'
        verbose_name_plural = 'Cluster attività'

    def __str__(self):
        return f"{self.get_categoria_display()} – {self.descrizione[:60]}"


class RegolaKeyword(models.Model):
    keyword = models.CharField(max_length=200, unique=True)
    categoria = models.CharField(max_length=50)

    class Meta:
        ordering = ['categoria', 'keyword']
        verbose_name = 'Regola keyword'
        verbose_name_plural = 'Regole keyword'

    def __str__(self):
        return f'{self.keyword} → {self.get_categoria_display()}'
