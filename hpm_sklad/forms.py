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
    "objednano", "nazev_dilu", "mnozstvi", "jednotky", "umisteni", "dodavatel",
    "datum_nakupu", "cislo_objednavky", "jednotkova_cena_eur", "celkova_cena_eur", "poznamka",
    "hsh", "tq8", "tqf_xl1", "tqf_xl2", "dc_xl", "dac_xl1_2", "dl_xl", "dac", "lac_1",
    "lac_2", "ipsen_ene", "hsh_ene", "xl_ene1", "xl_ene2", "ipsen_w", "hsh_w", "kw", "kw1",
    "kw2", "kw3", "mikrof",
    ]

all_auditlog_fields = [
    "id", "ucetnictvi", "evidencni_cislo", "interne_cislo", "objednano", "nazev_dilu", "zmena_mnozstvi",  
    "mnozstvi", "jednotky", "typ_operace", "pouzite_zarizeni", "umisteni", "dodavatel",
    "datum_vydeje", "datum_nakupu", "cislo_objednavky", "jednotkova_cena_eur", "celkova_cena_eur", 
    "cas_vytvoreni", "operaci_provedl", "poznamka",  
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
            "interne_cislo", "min_mnozstvi_ks", "objednano", "nazev_dilu", "jednotky", "umisteni", 
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
                    *[Field(field) for field in self.Meta.fields[:7]],
                    css_class='form-column'  # Přiřazení CSS třídy pro levý sloupec
                ),
                Div(
                    *[Field(field) for field in self.Meta.fields[7:]],
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

        self.helper.layout = Layout(
            Div(Field(self.Meta.fields[0]), css_class='form-column'), 
            Submit('submit', 'Uložit', css_class="nav-item"),
            )


class SkladReceiptForm(forms.ModelForm):
    datum_nakupu = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True,
                                   label='Datum nákupu')
    dodavatel = forms.ModelChoiceField(queryset=Dodavatele.objects.all(), required=False,
                                       empty_label="Vyberte dodavatele")
        
    class Meta:
        model = Sklad
        fields = ["objednano", "umisteni", "dodavatel", "datum_nakupu", "cislo_objednavky",
                  "jednotkova_cena_eur", "poznamka",]

    def __init__(self, *args, **kwargs):
        super(SkladReceiptForm, self).__init__(*args, **kwargs)
        
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(*[Field(field) for field in self.Meta.fields], css_class='form-column')
            )

        self.fields['dodavatel'].required = True
        self.fields['cislo_objednavky'].required = True
        self.fields['datum_nakupu'].required = True
        self.fields['jednotkova_cena_eur'].required = True

    def clean_jednotkova_cena_eur(self):
        jednotkova_cena = self.cleaned_data.get('jednotkova_cena_eur')
        if jednotkova_cena <= 0.0:
            raise ValidationError('Jednotková cena musí být větší než nula.')
        return jednotkova_cena


class SkladDispatchForm(forms.ModelForm):      
    class Meta:
        model = Sklad
        fields = ["umisteni", "poznamka",]

    def __init__(self, *args, **kwargs):
        super(SkladDispatchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(*[Field(field) for field in self.Meta.fields], css_class='form-column'),
            )
        

class AuditLogReceiptForm(forms.ModelForm): 
    class Meta:
        model = AuditLog
        fields = ["zmena_mnozstvi",]

    def __init__(self, *args, **kwargs):
        super(AuditLogReceiptForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(*[Field(field) for field in self.Meta.fields], css_class='form-column')
            )

class AuditLogDispatchForm(forms.ModelForm):
    datum_vydeje = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True,
                                   label='Datum výdeje')
    pouzite_zarizeni = forms.ModelChoiceField(queryset=Zarizeni.objects.all(), required=True,
                                              empty_label="Vyberte zařízení", label="Pro zařízení")
   
    class Meta:
        model = AuditLog
        fields = [
            "zmena_mnozstvi", "pouzite_zarizeni", "datum_vydeje", 
            ]

    def __init__(self, *args, **kwargs):
        super(AuditLogDispatchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(*[Field(field) for field in self.Meta.fields], css_class='form-column')
            )
        self.fields['datum_vydeje'].required = True

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
