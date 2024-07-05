from django import forms
from .models import Sklad, AuditLog, Dodavatele, Zarizeni, Varianty, Poptavky, PoptavkaVarianty
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit
from crispy_forms.bootstrap import FormActions
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from datetime import date


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

        # Add form-label-sm class to all labels
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})
            field.label_suffix = ""
        
        self.helper.layout = Layout(
            Div(
                Div(
                    *[Field(field, css_class='form-control form-control-sm', label_class='form-label-sm') for field in self.Meta.fields[:8]],
                    css_class='form-column col mr-3 small'
                ),
                Div(
                    *[Field(field, css_class='form-control form-control-sm', label_class='form-label-sm') for field in self.Meta.fields[8:]],
                    css_class='form-column col-auto mr-3 small'
                ),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                css_class='d-flex justify-content-center mt-3'  
            )
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
        self.helper.form_class = 'form-grid'  
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                Div(
                    *[Field(field, css_class='form-control form-control-sm') for field in self.Meta.fields[:7]],
                    css_class='form-column col mr-3 small'
                ),
                Div(
                    *[Field(field, css_class='form-control form-control-sm') for field in self.Meta.fields[7:]],
                    css_class='form-column col-auto mr-3 small'
                ),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                css_class='d-flex justify-content-center mt-3' 
            )
        )


class SkladUpdateObjednanoForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = ["objednano", ]

    def __init__(self, *args, **kwargs):
        super(SkladUpdateObjednanoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'  
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                Div('objednano', css_class='form-column small'),
                Div(Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                    css_class='d-flex justify-content-center mt-3'
                    )
                )
            )  

class SkladReceiptForm(forms.ModelForm):
    datum_nakupu = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
        required=True,
        label='Datum nákupu'
    )
    dodavatel = forms.ModelChoiceField(queryset=Dodavatele.objects.all(), required=True, empty_label="Vyberte dodavatele")
        
    class Meta:
        model = Sklad
        fields = ["objednano", "umisteni", "dodavatel", "datum_nakupu", "cislo_objednavky",
                  "jednotkova_cena_eur", "poznamka",]
        widgets = {
            'jednotkova_cena_eur': forms.NumberInput(attrs={'min': '0.001'}),
            }        

    def __init__(self, *args, **kwargs):
        super(SkladReceiptForm, self).__init__(*args, **kwargs)
        
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                *[Field(field, css_class='form-control form-control-sm') for field in self.Meta.fields],
                css_class='form-column col-auto mr-3 small'
                ),
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
            Div(*[Field(field, css_class='form-control form-control-sm', label_class='form-label-sm') for field in self.Meta.fields], css_class='form-column small'),
        )
        

class AuditLogReceiptForm(forms.ModelForm):
    zmena_mnozstvi = forms.IntegerField(validators=[MinValueValidator(1)], label='Změna množství')
    
    class Meta:
        model = AuditLog
        fields = ["zmena_mnozstvi",]

    def __init__(self, *args, **kwargs):
        super(AuditLogReceiptForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                *[Field(field, css_class='form-control form-control-sm') for field in self.Meta.fields],
                css_class='form-column col-auto mr-3 small'
                ),
            )


class AuditLogDispatchForm(forms.ModelForm):
    datum_vydeje = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
        required=True,
        label='Datum výdeje'
        )
    pouzite_zarizeni = forms.ModelChoiceField(queryset=Zarizeni.objects.all(), required=True, empty_label="Vyberte zařízení", label="Pro zařízení")
    zmena_mnozstvi = forms.ChoiceField(label='Změna množství')
   
    class Meta:
        model = AuditLog
        fields = ["zmena_mnozstvi", "pouzite_zarizeni", "datum_vydeje"]

    def __init__(self, *args, **kwargs):
        max_mnozstvi = kwargs.pop('max_mnozstvi', 1)
        super(AuditLogDispatchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(*[Field(field) for field in self.Meta.fields], css_class='form-column small', label_class='form-label-sm'),
            )
        
        self.fields['datum_vydeje'].required = True
        self.fields['zmena_mnozstvi'].choices = [(i, str(i)) for i in range(1, int(max_mnozstvi) + 1)]
      

class VariantyCreateForm(forms.ModelForm):
    class Meta:
        model = Varianty
        fields = ["nazev_varianty", "cislo_varianty", "jednotkova_cena_eur", "dodaci_lhuta",
                  "min_obj_mnozstvi", "dodavatel",]
        widgets = {
            'jednotkova_cena_eur': forms.NumberInput(attrs={'min': '0'}),
            }
    def __init__(self, *args, **kwargs):
        super(VariantyCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div(*[Field(field) for field in self.Meta.fields], css_class='form-column small'),
                Div(Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                    css_class='d-flex justify-content-center mt-3'
                    )
                )
            )  


class VariantyUpdateForm(forms.ModelForm):   
    class Meta:
        model = Varianty
        fields = ["nazev_varianty", "cislo_varianty", "jednotkova_cena_eur", "dodaci_lhuta", "min_obj_mnozstvi", ]

    def __init__(self, *args, **kwargs):
        super(VariantyUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-grid'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div(*[Field(field) for field in self.Meta.fields], css_class='form-column small'),
                Div(Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                    css_class='d-flex justify-content-center mt-3'
                    )
                )
            )        


class PoptavkaVariantyForm(forms.ModelForm):
    should_save = forms.BooleanField(required=False, label='Do poptávky')
    
    class Meta:
        model = PoptavkaVarianty
        fields = ['varianta', 'mnozstvi', 'jednotky']

    def __init__(self, *args, **kwargs):
        super(PoptavkaVariantyForm, self).__init__(*args, **kwargs)
        self.fields['varianta'].widget.attrs['disabled'] = 'disabled'
        
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-inline my-2 mx-2'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div(Field('varianta', css_class='form-control small mx-2', label_class="invisible"), css_class='col small'),
                Div(Field('mnozstvi', css_class='form-control mx-2 w-100'), css_class='col small'),
                Div(Field('jednotky', css_class='form-control form-control-sm mx-2'), css_class='col small'),
                Div(Field('should_save', css_class='form-check-input mx-2'), css_class='form-check mr-4 align-self-start'),
                css_class='row small',
            )
        )
        

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


