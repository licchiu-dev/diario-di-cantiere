from django import forms
from .models import GiornataDiario, Cantiere


class GiornataDiarioForm(forms.ModelForm):
    class Meta:
        model = GiornataDiario
        fields = [
            'data', 'cantiere', 'n_operai', 'ore_lavorate',
            'desc_preventivo', 'desc_extra', 'desc_materiali',
        ]
        widgets = {
            'data': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control form-control-lg'}
            ),
            'cantiere': forms.Select(
                attrs={'class': 'form-select form-select-lg'}
            ),
            'n_operai': forms.NumberInput(
                attrs={'class': 'form-control form-control-lg', 'min': '1', 'max': '50'}
            ),
            'ore_lavorate': forms.NumberInput(
                attrs={'class': 'form-control form-control-lg', 'step': '0.5', 'min': '1', 'max': '14'}
            ),
            'desc_preventivo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Es: Costruzione pareti cartongesso piano terra, stuccatura Q3 bagno padronale, prima mano pittura corridoio...',
                }
            ),
            'desc_extra': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Es: Spostamento materiali non previsto, attesa consegna profili, ritardo per mancanza elettricità...',
                }
            ),
            'desc_materiali': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Es: Bolla 234 – 50 lastre GKB 12.5, 20 sacchi Knauf finitura, 10 litri idropittura...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        cantiere_pk = kwargs.pop('cantiere_pk', None)
        super().__init__(*args, **kwargs)
        self.fields['cantiere'].queryset = Cantiere.objects.all()
        if cantiere_pk:
            self.initial.setdefault('cantiere', cantiere_pk)


class CantiereForm(forms.ModelForm):
    class Meta:
        model = Cantiere
        fields = ['nome', 'cliente', 'indirizzo', 'stato', 'data_inizio', 'note']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'data_inizio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
