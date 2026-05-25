from django.db import migrations

CATEGORIE = [
    {
        'key': 'cartongesso', 'nome': 'Cartongesso', 'tema': 'blu', 'ordine': 1,
        'keywords': (
            'cartongesso\nlastra\nlastre\ngkb\ngkf\nparete cg\npareti cg\n'
            'divisoria\ndivisorie\ncontroparete\ncontropareti\ncontrosoffitto\n'
            'veletta\ngola led\ngola luce\nprofilo\nmontante\ntraverso\nstruttura metallica'
        ),
    },
    {
        'key': 'finitura', 'nome': 'Finitura / Stuccatura', 'tema': 'verde', 'ordine': 2,
        'keywords': (
            'stucco\nstuccatura\nstuccare\nrasatura\nrasare\nq2\nq3\nq4\n'
            'livello 2\nlivello 3\nlivello 4\ngiunti\nnastro\nrinforzo angoli\n'
            'angolari\nfinitura\nlisciatura\nintonaco\nintonaci\nintonacare\n'
            'intonacatura\nrifacimento intonaco\nripristino intonaco\nstabilitura\n'
            'arriccio\nrinzaffo\nspigoli\nraccordo'
        ),
    },
    {
        'key': 'pittura', 'nome': 'Pittura', 'tema': 'giallo', 'ordine': 3,
        'keywords': (
            'pittura\ntinteggiatura\nverniciatura\ndipingere\nprima mano\n'
            'seconda mano\n1 mano\n2 mano\nfissativo\nfondo\nimpregnante\n'
            'primer\nidropittura\nquarzo'
        ),
    },
    {
        'key': 'resina', 'nome': 'Resina / Microcemento', 'tema': 'viola', 'ordine': 4,
        'keywords': (
            'resina\nmicrocemento\nmicrotopping\npavimento resinoso\n'
            'rivestimento resinoso\nprimer epossidico'
        ),
    },
    {
        'key': 'extra', 'nome': 'Extra / Non preventivato', 'tema': 'rosso', 'ordine': 5,
        'keywords': (
            'extra\nimprevisto\nnon previsto\nnon preventivato\nproblema\n'
            'fermo\nfermi\nattesa\nritardo\nmanca\nmancano\nbloccato\n'
            'infiltrazione\numidità\ncrack\ncrepa\ndifetto\ncorrezione'
        ),
    },
    {
        'key': 'materiali', 'nome': 'Materiali / Bolle', 'tema': 'arancio', 'ordine': 6,
        'keywords': '',
    },
    {
        'key': 'logistica', 'nome': 'Logistica', 'tema': 'teal', 'ordine': 7,
        'keywords': (
            'deposito\nscarico\ncarico\ntrasporto\nmovimentazione\n'
            'portato in cantiere\nsposta\nspostamento materiali\n'
            'pulizia\nriordino\nsgombero'
        ),
    },
    {
        'key': 'altro', 'nome': 'Altro', 'tema': 'grigio', 'ordine': 8,
        'keywords': '',
    },
]


def crea_categorie(apps, schema_editor):
    CategoriaLavorazione = apps.get_model('core', 'CategoriaLavorazione')
    for c in CATEGORIE:
        CategoriaLavorazione.objects.get_or_create(key=c['key'], defaults=c)


def rimuovi_categorie(apps, schema_editor):
    CategoriaLavorazione = apps.get_model('core', 'CategoriaLavorazione')
    CategoriaLavorazione.objects.filter(key__in=[c['key'] for c in CATEGORIE]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_categorialavorazione_alter_clusterattivita_categoria_and_more'),
    ]

    operations = [
        migrations.RunPython(crea_categorie, rimuovi_categorie),
    ]
