from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from simple_history.models import HistoricalRecords

class Sklad(models.Model):
    JEDNOTKY_CHOICES = [
        ('ks', 'kus'),
        ('kg', 'kilogram'),
        ('par', 'pár'),
        ('l', 'litr'),
        ('m', 'metr'),
        ('baleni', 'balení'),
    ]

    evidencni_cislo = models.IntegerField(primary_key=True, verbose_name="Evidenční číslo")
    interne_cislo = models.IntegerField(null=True, verbose_name="Číslo karty")  
    objednano = models.CharField(max_length=100, null=True, blank=True, verbose_name="Objednáno?")
    nazev_dilu = models.CharField(max_length=100, verbose_name="Název dílu")
    min_mnozstvi_ks = models.PositiveIntegerField(default=0, verbose_name="Minimum")
    mnozstvi_ks_m_l = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, default='ks', verbose_name="Jednotky")
    umisteni = models.CharField(max_length=25, verbose_name="Umístění")
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

class Dodavatele(models.Model):
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
    zarizeni = models.CharField(max_length=10, verbose_name="Zařízení")
    nazev_zarizeni = models.CharField(max_length=100, verbose_name="Název zařízení")
    umisteni = models.CharField(max_length=20, verbose_name="Umístění")
    typ_zarizeni = models.CharField(max_length=100, verbose_name="Typ zařízení")


    def __str__(self):
        return f"{self.nazev_zarizeni}: {self.umisteni}"
    
class AuditLog(models.Model):
    MOVEMENT_CHOICES = [
        ('IN', 'Příjem'),
        ('OUT', 'Výdej')
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
    evidencni_cislo = models.ForeignKey(Sklad, on_delete=models.CASCADE)
    interne_cislo = models.IntegerField(null=True, verbose_name="Číslo karty")
    objednano = models.CharField(max_length=100, null=True, blank=True, verbose_name="Objednáno?")
    nazev_dilu = models.CharField(max_length=100, verbose_name="Název dílu")
    zmena_mnozstvi = models.PositiveIntegerField(verbose_name="Změna množství")
    mnozstvi_ks_m_l = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, default='ks', verbose_name="Jednotky")
    typ_operace = models.CharField(max_length=10, choices=MOVEMENT_CHOICES, verbose_name="Typ operace")
    pouzite_zarizeni = models.CharField(max_length=70, verbose_name="Pro zařízení")
    umisteni = models.CharField(max_length=25, verbose_name="Umístění")
    dodavatel = models.CharField(max_length=70, verbose_name="Dodavatel")
    datum_zmeny = models.DateField(verbose_name="Datum změny")
    cislo_objednavky = models.CharField(max_length=20, null=True, blank=True, verbose_name="Číslo objednávky")
    jednotkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="EUR/jednotka")
    celkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="Celkem EUR")
    cas_vytvoreni = models.DateTimeField(auto_now_add=True, verbose_name="Čas vytvoření")
    operaci_provedl = models.CharField(max_length=20, verbose_name="Operaci provedl")
    poznamka = models.CharField(null=True, blank=True, max_length=200, verbose_name="Poznámka")

    def __str__(self):
        return f"{self.movement_type}: {self.quantity}x {self.spare_part}"

