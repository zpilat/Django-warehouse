from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords


class Sklad(models.Model):
    class Meta:
        ordering = ["-evidencni_cislo"]
        verbose_name_plural = "Skladové položky"

    JEDNOTKY_CHOICES = [
        ('ks', 'kus'),
        ('kg', 'kilogram'),
        ('par', 'pár'),
        ('l', 'litr'),
        ('m', 'metr'),
        ('baleni', 'balení'),
    ]

    evidencni_cislo = models.AutoField(primary_key=True, verbose_name="Evidenční číslo")
    interne_cislo = models.IntegerField(null=True, verbose_name="Číslo karty")  
    objednano = models.CharField(max_length=100, null=True, blank=True, verbose_name="Objednáno?")
    nazev_dilu = models.CharField(max_length=100, verbose_name="Název dílu")
    min_mnozstvi_ks = models.PositiveIntegerField(default=0, verbose_name="Minimum")
    mnozstvi = models.PositiveIntegerField(default=0, verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, default='ks', verbose_name="Jednotky")
    umisteni = models.CharField(max_length=25, null=True, verbose_name="Umístění")
    dodavatel = models.CharField(max_length=70, null=True, blank=True, verbose_name="Dodavatel")
    datum_nakupu = models.DateField(null=True, blank=True, verbose_name="Datum nákupu")
    cislo_objednavky = models.CharField(max_length=20, null=True, blank=True, verbose_name="Číslo objednávky")
    jednotkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="EUR/jednotka")
    celkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="Celkem EUR")
    poznamka = models.CharField(null=True, blank=True, max_length=200, verbose_name="Poznámka")
    ucetnictvi = models.BooleanField(default=True, verbose_name="Účetnictví")
    kriticky_dil = models.BooleanField(default=False, verbose_name="Kritický díl") 
    hsh = models.BooleanField(default=False, verbose_name="HSH")
    tq8 = models.BooleanField(default=False, verbose_name="TQ8")
    tqf_xl1 = models.BooleanField(default=False, verbose_name="TQF XL1")
    tqf_xl2 = models.BooleanField(default=False, verbose_name="TQF XL2")
    dc_xl = models.BooleanField(default=False, verbose_name="DC XL")
    dac_xl1_2 = models.BooleanField(default=False, verbose_name="DAC XL1-2")
    dl_xl = models.BooleanField(default=False, verbose_name="DL XL")
    dac = models.BooleanField(default=False, verbose_name="DAC")
    lac_1 = models.BooleanField(default=False, verbose_name="LAC 1")
    lac_2 = models.BooleanField(default=False, verbose_name="LAC 2")
    ipsen_ene = models.BooleanField(default=False, verbose_name="IPSEN ENE")
    hsh_ene = models.BooleanField(default=False, verbose_name="HSH ENE")
    xl_ene1 = models.BooleanField(default=False, verbose_name="XL ENE1")
    xl_ene2 = models.BooleanField(default=False, verbose_name="XL ENE2")
    ipsen_w = models.BooleanField(default=False, verbose_name="IPSEN W")
    hsh_w = models.BooleanField(default=False, verbose_name="HSH W")
    kw = models.BooleanField(default=False, verbose_name="KW")
    kw1 = models.BooleanField(default=False, verbose_name="KW 1")
    kw2 = models.BooleanField(default=False, verbose_name="KW 2")
    kw3 = models.BooleanField(default=False, verbose_name="KW 3")
    mikrof = models.BooleanField(default=False, verbose_name="MIKROF")
    history = HistoricalRecords()

    def get_absolute_url(self):
        return reverse("sklad")
    
    def __str__(self):
        return "Evid. č. " + str(self.evidencni_cislo) + ", " + self.nazev_dilu

    @property
    def pod_minimem(self):
        return self.mnozstvi < self.min_mnozstvi_ks

    def pod_minimem_display(self):
        return "ANO" if self.pod_minimem else "NE"


class Dodavatele(models.Model):
    class Meta:
        verbose_name_plural = "Dodavatelé"
    
    LANGUAGE_CHOICES = [
        ('CZ', 'Český'),
        ('SK', 'Slovenský'),
        ('DE', 'Německý'),
        ('EN', 'Anglický')
    ]
    dodavatel = models.CharField(max_length=100, verbose_name="Dodavatel")
    kontakt = models.CharField(null=True, max_length=100, verbose_name="Kontaktní osoba")
    email = models.EmailField(null=True, max_length=100, verbose_name="E-mail")
    telefon = models.CharField(null=True, max_length=20, verbose_name="Telefon")
    jazyk = models.CharField(null=True, max_length=2, choices=LANGUAGE_CHOICES, default='CZ', verbose_name="Jazyk") 

    def __str__(self):
        return f"{self.dodavatel}"


class Zarizeni(models.Model):
    class Meta:
        verbose_name_plural = "Zařízení"
    
    zarizeni = models.CharField(max_length=10, verbose_name="Zařízení")
    nazev_zarizeni = models.CharField(max_length=100, verbose_name="Název zařízení")
    umisteni = models.CharField(max_length=20, verbose_name="Umístění")
    typ_zarizeni = models.CharField(max_length=100, verbose_name="Typ zařízení")


    def __str__(self):
        return f"{self.zarizeni}"

    
class AuditLog(models.Model):
    class Meta:
        verbose_name_plural = "Auditovací logy"
        ordering = ["-id"]
    
    MOVEMENT_CHOICES = [
        ('PŘÍJEM', 'Příjem'),
        ('VÝDEJ', 'Výdej')
    ]

    JEDNOTKY_CHOICES = [
        ('ks', 'kus'),
        ('kg', 'kilogram'),
        ('par', 'pár'),
        ('l', 'litr'),
        ('m', 'metr'),
        ('baleni', 'balení'),
    ]
    
    ucetnictvi = models.BooleanField(verbose_name="Účetnictví")
    evidencni_cislo = models.ForeignKey(Sklad, on_delete=models.CASCADE, verbose_name="Evidenční číslo")
    interne_cislo = models.IntegerField(null=True, verbose_name="Číslo karty")
    objednano = models.CharField(max_length=100, null=True, blank=True, verbose_name="Objednáno?")
    nazev_dilu = models.CharField(max_length=100, verbose_name="Název dílu", db_index=True)
    zmena_mnozstvi = models.IntegerField(verbose_name="Změna množství")
    mnozstvi = models.PositiveIntegerField(verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, default='ks', verbose_name="Jednotky")
    typ_operace = models.CharField(max_length=10, choices=MOVEMENT_CHOICES, verbose_name="Typ operace")
    pouzite_zarizeni = models.CharField(max_length=70, null=True, verbose_name="Pro zařízení")
    umisteni = models.CharField(max_length=25, verbose_name="Umístění")
    dodavatel = models.CharField(max_length=70, verbose_name="Dodavatel")
    datum_vydeje = models.DateField(null=True, blank=True, verbose_name="Datum výdeje")
    datum_nakupu = models.DateField(null=True, blank=True, verbose_name="Datum nákupu")
    cislo_objednavky = models.CharField(max_length=20, null=True, blank=True, verbose_name="Číslo objednávky")
    jednotkova_cena_eur = models.FloatField(default=0.0, verbose_name="EUR/jednotka")
    celkova_cena_eur = models.FloatField(default=0.0, verbose_name="Celkem EUR")
    cas_vytvoreni = models.DateTimeField(auto_now_add=True, verbose_name="Čas vytvoření")
    operaci_provedl = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Operaci provedl")
    poznamka = models.CharField(null=True, blank=True, max_length=200, verbose_name="Poznámka")

    def __str__(self):
        return f"{self.typ_operace}: {self.zmena_mnozstvi}x {self.nazev_dilu}"


class Varianty(models.Model):

    sklad = models.ForeignKey(Sklad, on_delete=models.CASCADE, related_name='varianty_skladu', verbose_name="Skladová položka")
    dodavatel = models.ForeignKey(Dodavatele, on_delete=models.CASCADE, related_name='varianty_dodavatele', verbose_name="Dodavatel")
    nazev_varianty = models.CharField(max_length=255, verbose_name="Název varianty")
    cislo_varianty = models.CharField(max_length=255, null=True, verbose_name="Číslo varianty")
    jednotkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="EUR/jednotka")
    dodaci_lhuta = models.PositiveIntegerField(verbose_name="Dodací lhůta")
    min_obj_mnozstvi = models.PositiveIntegerField(verbose_name="Min. obj. množství")

    class Meta:
        verbose_name_plural = 'Varianty'
        verbose_name = 'Varianta'
 
    def __str__(self):
        return self.nazev_varianty
    

class Poptavky(models.Model):
    class Meta:
        verbose_name_plural = 'Poptávky'
        verbose_name = 'Poptávka'

    STAVY_CHOICES = [
        ('Tvorba', 'Ve tvorbě'),
        ('Poptáno', 'Poptáno'),
        ('Uzavřeno', 'Uzavřeno'),
        ]

    dodavatel = models.ForeignKey(Dodavatele, on_delete=models.CASCADE, related_name='poptavky', verbose_name="Dodavatel")
    datum_vytvoreni = models.DateTimeField(auto_now_add=True, verbose_name="Datum vytvoření")
    stav = models.CharField(max_length=10, choices=STAVY_CHOICES, default='Tvorba', verbose_name="Stav poptávky")
    varianty = models.ManyToManyField('Varianty', through='PoptavkaVarianty')

    def __str__(self):
        return f"Poptávka #{self.id} u dodavatele: {self.dodavatel.dodavatel}"
    

class PoptavkaVarianty(models.Model):
    JEDNOTKY_CHOICES = [
        ('ks', 'kus'),
        ('kg', 'kilogram'),
        ('par', 'pár'),
        ('l', 'litr'),
        ('m', 'metr'),
        ('baleni', 'balení'),
    ]
    
    poptavka = models.ForeignKey(Poptavky, on_delete=models.CASCADE, verbose_name="Poptávka")
    varianta = models.ForeignKey(Varianty, on_delete=models.CASCADE, verbose_name="Varianta")
    mnozstvi = models.PositiveIntegerField(verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, verbose_name="Jednotky")

    def __str__(self):
        return f"{self.poptavka} - {self.varianta} - {self.mnozstvi} {self.jednotky}"
