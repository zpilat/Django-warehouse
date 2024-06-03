from django import forms
from .models import Sklad, AuditLog, Dodavatele, Zarizeni
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit
from crispy_forms.bootstrap import FormActions
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


all_sklad_fields = [
    "evidencni_cislo", "ucetnictvi", "kriticky_dil", "interne_cislo", "min_mnozstvi_ks",
    "objednano", "nazev_dilu", "mnozstvi_ks_m_l", "jednotky", "umisteni", "dodavatel",
    "datum_nakupu", "cislo_objednavky", "jednotkova_cena_eur", "celkova_cena_eur", "poznamka",
    "hsh", "tq8", "tqf_xl1", "tqf_xl2", "dc_xl", "dac_xl1_2", "dl_xl", "dac", "lac_1",
    "lac_2", "ipsen_ene", "hsh_ene", "xl_ene1", "xl_ene2", "ipsen_w", "hsh_w", "kw", "kw1",
    "kw2", "kw3", "mikrof",
    ]

class SkladCreateForm(forms.ModelForm):
    dodavatel = forms.ModelChoiceField(queryset=Dodavatele.objects.all(), required=False, empty_label="Vyberte dodavatele")

    class Meta:
        model = Sklad
        fields = [
            "interne_cislo", "min_mnozstvi_ks", "objednano", "nazev_dilu", "jednotky", "umisteni", "dodavatel",
            "poznamka", "ucetnictvi", "kriticky_dil", "hsh", "tq8", "tqf_xl1", "tqf_xl2", "dc_xl", "dac_xl1_2",
            "dl_xl", "dac", "lac_1", "lac_2", "ipsen_ene", "hsh_ene", "xl_ene1", "xl_ene2", "ipsen_w", "hsh_w",
            "kw", "kw1", "kw2", "kw3", "mikrof"
        ]

    def __init__(self, *args, **kwargs):
        super(SkladCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-grid'

        max_interne_cislo = Sklad.objects.aggregate(models.Max('interne_cislo'))['interne_cislo__max']
        initial_interne_cislo = (max_interne_cislo or 0) + 1
        self.fields['interne_cislo'].initial = initial_interne_cislo

        # Vytvoření layoutu s dvěma sloupci
        self.helper.layout = Layout(
            Div(
                Div(
                    *[Field(field) for field in self.Meta.fields[:8]],
                    css_class='form-column'
                ),
                Div(
                    *[Field(field) for field in self.Meta.fields[8:]],
                    css_class='form-column'
                ),
                css_class='row'
            ),
            Submit('submit', 'Uložit', css_class="nav-item")
        )


class SkladUpdateForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = [
            "interne_cislo", "min_mnozstvi_ks", "objednano", "jednotky", "umisteni", 
            "poznamka", "ucetnictvi", "kriticky_dil", "hsh", "tq8", "tqf_xl1", "tqf_xl2",
            "dc_xl", "dac_xl1_2", "dl_xl", "dac", "lac_1", "lac_2", "ipsen_ene", "hsh_ene",
            "xl_ene1", "xl_ene2", "ipsen_w", "hsh_w", "kw", "kw1", "kw2", "kw3", "mikrof"
            ]

    def __init__(self, *args, **kwargs):
        super(SkladUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'  # Přiřazení CSS třídy pro grid layout
        self.helper.form_method = 'post'

        # Vytvoření layoutu s dvěma sloupci
        self.helper.layout = Layout(
            Div(
                Div(
                    *[Field(field) for field in self.Meta.fields[:6]],
                    css_class='form-column'  # Přiřazení CSS třídy pro levý sloupec
                ),
                Div(
                    *[Field(field) for field in self.Meta.fields[6:]],
                    css_class='form-column'  # Přiřazení CSS třídy pro pravý sloupec
                ),
                css_class='row'  # Přiřazení CSS třídy pro obalový div sloupců
            ),
            Submit('submit', 'Uložit', css_class="nav-item")
        )


class SkladUpdateObjednanoForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = ["objednano", ]

    def __init__(self, *args, **kwargs):
        super(SkladUpdateObjednanoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'  # Přiřazení CSS třídy pro grid layout
        self.helper.form_method = 'post'

        # Vytvoření layoutu s dvěma sloupci
        self.helper.layout = Layout(
            Div(Field(self.Meta.fields[0]), css_class='form-column'), 
            Submit('submit', 'Uložit', css_class="nav-item"),
            )

        
class SkladReceiptUpdateForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = [
            "evidencni_cislo", "interne_cislo", "ucetnictvi", "objednano", "nazev_dilu",
            "mnozstvi_ks_m_l", "jednotky", "umisteni", "dodavatel", "datum_nakupu",
            "cislo_objednavky", "jednotkova_cena_eur", "celkova_cena_eur", "poznamka",
            ]

    def __init__(self, *args, **kwargs):
        super(SkladReceiptUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                *[Field(field) for field in self.Meta.fields],
                css_class='form-column'
            )
        )  


class AuditLogCreateForm(forms.ModelForm):
    datum_operace = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now,
        required=True
    )
    
    class Meta:
        model = AuditLog
        fields = [
            "zmena_mnozstvi", "typ_operace", "pouzite_zarizeni",
            ]

    def __init__(self, *args, **kwargs):
        super(AuditLogCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                *[Field(field) for field in self.Meta.fields],
                css_class='form-column'
            )
        )  


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
