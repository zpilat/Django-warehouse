class SkladCreateForm(forms.ModelForm):
    """
    Formulář pro vytvoření nového záznamu ve skladu.
    Tento formulář zahrnuje pole pro zadávání interního čísla, minimálního množství, objednaných dílů,
    názvu dílu, jednotek, umístění, dodavatele a dalších atributů specifických pro skladové položky.
    """
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
    """
    Formulář pro aktualizaci existujícího záznamu ve skladu.
    Umožňuje úpravu položek jako je interní číslo, množství, název dílu, jednotky a další.
    """
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
    """
    Formulář pro aktualizaci pole 'objednáno' ve skladové položce.
    Používá se pro zaznamenání objednaných dílů bez úpravy jiných atributů skladové položky.
    """
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
                Div(Field('objednano', css_class='form-control form-control-sm'), css_class='form-column small'),
                Div(Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                    css_class='d-flex justify-content-center mt-3'
                    )
                )
            )  


class SkladReceiptForm(forms.ModelForm):
    """
    Formulář pro příjem nové položky na sklad.
    Obsahuje pole pro datum nákupu, dodavatele, číslo objednávky, jednotkovou cenu a další informace spojené s příjmem na sklad.
    """
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
        """
        Ověření, že jednotková cena je větší než nula.
        """
        jednotkova_cena = self.cleaned_data.get('jednotkova_cena_eur')
        if jednotkova_cena <= 0.0:
            raise ValidationError('Jednotková cena musí být větší než nula.')
        return jednotkova_cena


class SkladDispatchForm(forms.ModelForm):
    """
    Formulář pro výdej položky ze skladu.
    Umožňuje zaznamenat umístění a poznámku k výdeji.
    """
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
    """
    Formulář pro zaznamenání příjmu zboží v audit logu.
    Obsahuje pole pro zadání změny množství přijatého zboží.
    """
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
    """
    Formulář pro zaznamenání výdeje zboží v audit logu.
    Obsahuje pole pro zadání data výdeje, použitého zařízení a změny množství.
    """
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
    """
    Formulář pro vytvoření nové varianty produktu.
    Obsahuje pole pro název, číslo varianty, jednotkovou cenu, dodací lhůtu, minimální objednací množství a dodavatele.
    """
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
    """
    Formulář pro aktualizaci existující varianty produktu.
    Obsahuje pole pro název varianty, číslo varianty, jednotkovou cenu, dodací lhůtu a minimální objednací množství.
    """
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


class DodavateleCreateForm(forms.ModelForm):
    """
    Formulář pro vytvoření nového dodavatele.
    Obsahuje pole pro zadání jména dodavatele, kontaktu, e-mailu, telefonního čísla a jazyka komunikace.
    """
    class Meta:
        model = Dodavatele
        fields = [
            "dodavatel", "kontakt", "email", "telefon", "jazyk",
        ]

    def __init__(self, *args, **kwargs):
        super(DodavateleCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-grid'

        # Add form-label-sm class to all labels
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})
            field.label_suffix = ""
        
        self.helper.layout = Layout(
            Div(
                Div(*[Field(field) for field in self.Meta.fields], css_class='form-column small'),
                Div(Submit('submit', 'Uložit', css_class="btn btn-sm btn-dark rounded-pill"),
                    css_class='d-flex justify-content-center mt-3'
                    )
                )
            )  


class DodavateleUpdateForm(forms.ModelForm):
    """
    Formulář pro aktualizaci existujícího dodavatele.
    Obsahuje pole pro úpravu kontaktu, e-mailu, telefonního čísla a jazyka komunikace.
    """
    class Meta:
        model = Dodavatele
        fields = [
            "kontakt", "email", "telefon", "jazyk",
        ]

    def __init__(self, *args, **kwargs):
        super(DodavateleUpdateForm, self).__init__(*args, **kwargs)
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
    """
    Formulář pro přidání varianty do poptávky.
    Umožňuje vybrat variantu produktu, množství a jednotky.
    """
    should_save = forms.BooleanField(required=False, label='Do poptávky')

    class Meta:
        model = PoptavkaVarianty
        fields = ['varianta', 'mnozstvi', 'jednotky']
        widgets = {
            'varianta': forms.HiddenInput(),
            'jednotky': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        varianty_dodavatele = kwargs.pop('varianty_dodavatele', None)
        super(PoptavkaVariantyForm, self).__init__(*args, **kwargs)
        if varianty_dodavatele is not None:
            self.fields['varianta'].queryset = varianty_dodavatele
        self.fields['mnozstvi'].widget.attrs.update({'class': 'form-control form-control-sm w-75'})

    def clean_jednotky(self):
        """
        Ověření, že zadaná hodnota jednotek je platná.
        """
        jednotky = self.cleaned_data.get('jednotky')
        valid_choices = dict(JEDNOTKY_CHOICES).keys()
        if jednotky not in valid_choices:
            raise forms.ValidationError("Neplatná hodnota pro jednotky.")
        return jednotky


class CustomUserCreationForm(UserCreationForm):
    """
    Vlastní formulář pro vytvoření nového uživatelského účtu.
    Kromě uživatelského jména a hesla vyžaduje i zadání e-mailové adresy.
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
