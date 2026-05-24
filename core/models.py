from django.db import models
from django.urls import reverse


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


class ClusterAttivita(models.Model):
    CATEGORIA_CHOICES = [
        ('cartongesso', 'Cartongesso'),
        ('finitura', 'Finitura / Stuccatura'),
        ('pittura', 'Pittura'),
        ('resina', 'Resina / Microcemento'),
        ('extra', 'Extra / Non preventivato'),
        ('materiali', 'Materiali / Bolle'),
        ('logistica', 'Logistica'),
        ('altro', 'Altro'),
    ]
    FONTE_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('extra', 'Extra'),
        ('materiali', 'Materiali'),
    ]
    giornata = models.ForeignKey(
        GiornataDiario, on_delete=models.CASCADE, related_name='clusters'
    )
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='altro')
    descrizione = models.TextField()
    ore_stimate = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    class Meta:
        ordering = ['categoria']
        verbose_name = 'Cluster attività'
        verbose_name_plural = 'Cluster attività'

    def __str__(self):
        return f"{self.get_categoria_display()} – {self.descrizione[:60]}"
