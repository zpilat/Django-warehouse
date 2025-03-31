from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

JEDNOTKY_CHOICES = [
        ('ks', 'kus'),
        ('kg', 'kilogram'),
        ('pár', 'pár'),
        ('l', 'litr'),
        ('m', 'metr'),
        ('balení', 'balení'),
    ]


class Zarizeni(models.Model):
    """
    Model reprezentující zařízení.

    Pole:
    - zarizeni: Kód zařízení.
    - nazev_zarizeni: Název zařízení.
    - umisteni: Umístění zařízení.
    - typ_zarizeni: Typ zařízení.

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Zařízení".
    """
    class Meta:
        verbose_name_plural = "Zařízení"

    kod_zarizeni = models.CharField(max_length=10, verbose_name="Kód zařízení")
    nazev_zarizeni = models.CharField(max_length=100, verbose_name="Název zařízení")
    umisteni = models.CharField(max_length=20, verbose_name="Umístění")
    typ_zarizeni = models.CharField(max_length=100, verbose_name="Typ zařízení")

    def __str__(self):
        return f"{self.typ_zarizeni} {self.nazev_zarizeni}"


class Sklad(models.Model):
    """
    Model reprezentující skladovou položku.

    Pole:
    - evidencni_cislo: Primární klíč a evidenční číslo položky.
    - interne_cislo: Interní číslo položky, identifikátor karty.
    - objednano: Informace, zda je položka objednána.
    - nazev_dilu: Název dílu/položky.
    - min_mnozstvi_ks: Minimální požadované množství položky na skladě.
    - mnozstvi: Aktuální množství položky na skladě.
    - jednotky: Jednotky, ve kterých je množství položky měřeno (např. ks, kg, l).
    - umisteni: Umístění položky na skladě.
    - dodavatel: Dodavatel položky.
    - datum_nakupu: Datum nákupu položky.
    - cislo_objednavky: Číslo objednávky související s položkou.
    - jednotkova_cena_eur: Jednotková cena položky v eurech.
    - celkova_cena_eur: Celková cena položky v eurech.
    - poznamka: Další poznámky k položce.
    - ucetnictvi: Indikace, zda je položka v účetnictví.
    - kriticky_dil: Indikace, zda jde o kritický díl.
    - zarizeni: many to many pole k tabulce Zarizeni - zařízení, pro které je ND určen.  
    - history: Historie změn položky.

    Vlastnosti:
    - pod_minimem: Vlastnost vracející True, pokud je položka pod minimálním množstvím.
    - pod_minimem_display: Vrací řetězec 'ANO' nebo 'NE', podle toho, zda je položka pod minimem.

    Meta:
    - ordering: Záznamy jsou řazeny podle evidenčního čísla sestupně.
    - verbose_name_plural: Množné číslo názvu modelu je "Skladové položky".
    """
    class Meta:
        ordering = ["-evidencni_cislo"]
        verbose_name_plural = "Skladové položky"

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
    zarizeni = models.ManyToManyField(Zarizeni, blank=True, through='SkladZarizeni', verbose_name="Zařízení")
    history = HistoricalRecords()

    def get_absolute_url(self):
        return reverse("sklad")
    
    def __str__(self):
        return f"Evid. č. {str(self.evidencni_cislo)}, {self.nazev_dilu}"

    @property
    def pod_minimem(self):
        return self.mnozstvi < self.min_mnozstvi_ks

    def pod_minimem_display(self):
        return "ANO" if self.pod_minimem else "NE"


class SkladZarizeni(models.Model):
    """
    Propojovací model mezi skladovými položkami a zařízeními.

    Pole:
    - sklad: Odkaz na skladovou položku (cizí klíč na model Sklad).
    - zarizeni: Odkaz na zařízení (cizí klíč na model Zarizeni).

    Omezení:
    - Kombinace Sklad / Zarizeni musí být jedinečné v rámci této tabulky
    """

    class Meta:
        unique_together = ('sklad', 'zarizeni')
        verbose_name_plural = "Skladové položky - Zařízení"
    
    sklad = models.ForeignKey(Sklad, on_delete=models.CASCADE, verbose_name="Skladová položka")
    zarizeni = models.ForeignKey(Zarizeni, on_delete=models.CASCADE, verbose_name="Zařízení")

    def __str__(self):
        return f"{self.sklad} - {self.zarizeni}"
    

class Dodavatele(models.Model):
    """
    Model reprezentující dodavatele.

    Pole:
    - dodavatel: Název dodavatele.
    - kontakt: Kontaktní osoba u dodavatele.
    - email: E-mailová adresa kontaktní osoby.
    - telefon: Telefonní číslo kontaktní osoby.
    - jazyk: Preferovaný jazyk komunikace s dodavatelem (český, slovenský, německý, anglický).

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Dodavatelé".
    """
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
    

class AuditLog(models.Model):
    """
    Model pro sledování pohybů (příjem a výdej) položek ve skladu.

    Pole:
    - ucetnictvi: Indikace, zda je skladová položka v účetnictví.
    - evidencni_cislo: Odkaz na skladovou položku (cizí klíč na model Sklad).
    - interne_cislo: Interní číslo položky.
    - objednano: Informace, zda je položka objednána.
    - nazev_dilu: Název dílu/položky.
    - zmena_mnozstvi: Množství, o které se položka změnila (příjem/výdej).
    - mnozstvi: Aktuální množství položky po změně.
    - jednotky: Jednotky, ve kterých je změna měřena.
    - typ_operace: Typ operace (příjem nebo výdej).
    - pouzite_zarizeni: Zařízení, pro které byla položka použita.
    - umisteni: Umístění položky.
    - dodavatel: Dodavatel položky.
    - datum_vydeje: Datum výdeje položky.
    - datum_nakupu: Datum nákupu položky.
    - cislo_objednavky: Číslo objednávky.
    - jednotkova_cena_eur: Jednotková cena položky v eurech.
    - celkova_cena_eur: Celková cena položky v eurech po operaci.
    - cas_vytvoreni: Čas, kdy byla operace zaznamenána.
    - operaci_provedl: Uživatel, který operaci provedl.
    - typ_udrzby: Typ údržby (reaktivní, preventivní, prediktivní, ostatní).
    - poznamka: Další poznámky k operaci.

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Auditovací logy".
    - ordering: Záznamy jsou řazeny podle ID sestupně (nejnovější nahoře).
    """
    class Meta:
        verbose_name_plural = "Auditovací logy"
        ordering = ["-id"]
    
    MOVEMENT_CHOICES = [
        ('PŘÍJEM', 'Příjem'),
        ('VÝDEJ', 'Výdej')
    ]

    UDRZBA_CHOICES = [
        ('Reaktivní', 'Reaktivní'),
        ('Preventivní', 'Preventivní'),
        ('Prediktivní', 'Prediktivní'),
        ('Inventura', 'Inventurní rozdíl'),
    ]

    ucetnictvi = models.BooleanField(verbose_name="Účetnictví")
    evidencni_cislo = models.ForeignKey(Sklad, on_delete=models.CASCADE, verbose_name="Evidenční číslo")
    interne_cislo = models.IntegerField(null=True, verbose_name="Číslo karty")
    objednano = models.CharField(max_length=100, null=True, blank=True, verbose_name="Objednáno?")
    nazev_dilu = models.CharField(max_length=100, verbose_name="Název dílu", db_index=True)
    zmena_mnozstvi = models.IntegerField(verbose_name="Změna množství")
    mnozstvi = models.PositiveIntegerField(verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, default='ks', verbose_name="Jednotky")
    typ_operace = models.CharField(max_length=10, choices=MOVEMENT_CHOICES, null=True, verbose_name="Typ operace")
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
    typ_udrzby = models.CharField(max_length=20, choices=UDRZBA_CHOICES, null=True, verbose_name="Typ údržby")
    poznamka = models.CharField(null=True, blank=True, max_length=200, verbose_name="Poznámka")

    def __str__(self):
        return f"{self.typ_operace}: {self.zmena_mnozstvi}x {self.nazev_dilu}"


class Varianty(models.Model):
    """
    Model reprezentující variantu skladové položky.

    Pole:
    - sklad: Odkaz na skladovou položku (cizí klíč na model Sklad).
    - dodavatel: Odkaz na dodavatele (cizí klíč na model Dodavatele).
    - nazev_varianty: Název varianty.
    - cislo_varianty: Číslo varianty.
    - jednotkova_cena_eur: Jednotková cena varianty v eurech.
    - dodaci_lhuta: Dodací lhůta varianty v dnech.
    - min_obj_mnozstvi: Minimální objednatelné množství varianty.

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Varianty".
    """
    class Meta:
        verbose_name_plural = 'Varianty'
        verbose_name = 'Varianta'

    sklad = models.ForeignKey(Sklad, on_delete=models.CASCADE, related_name='varianty_skladu', verbose_name="Skladová položka")
    dodavatel = models.ForeignKey(Dodavatele, on_delete=models.CASCADE, related_name='varianty_dodavatele', verbose_name="Dodavatel")
    nazev_varianty = models.CharField(max_length=255, verbose_name="Název varianty")
    cislo_varianty = models.CharField(max_length=255, null=True, verbose_name="Číslo varianty")
    jednotkova_cena_eur = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)], verbose_name="EUR/jednotka")
    dodaci_lhuta = models.PositiveIntegerField(verbose_name="Dodací lhůta")
    min_obj_mnozstvi = models.PositiveIntegerField(verbose_name="Min. obj. množství")
 
    def __str__(self):
        return self.nazev_varianty[:60]
    

class Poptavky(models.Model):
    """
    Model reprezentující poptávku.

    Pole:
    - dodavatel: Odkaz na dodavatele, kterého se poptávka týká.
    - datum_vytvoreni: Datum vytvoření poptávky.
    - stav: Stav poptávky (např. Ve tvorbě, Poptáno, Uzavřeno).
    - varianty: Varianty, které jsou součástí poptávky.

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Poptávky".
    """
    class Meta:
        verbose_name_plural = 'Poptávky'
        verbose_name = 'Poptávka'

    STAVY_CHOICES = [
        ('Tvorba', 'Ve tvorbě'),
        ('Poptáno', 'Poptáno'),
        ('Uzavřeno', 'Uzavřeno'),
        ]

    dodavatel = models.ForeignKey(Dodavatele, on_delete=models.CASCADE, related_name='poptavky_dodavatele', verbose_name="Dodavatel")
    datum_vytvoreni = models.DateTimeField(auto_now_add=True, verbose_name="Datum vytvoření")
    stav = models.CharField(max_length=10, choices=STAVY_CHOICES, default='Tvorba', verbose_name="Stav poptávky")
    varianty = models.ManyToManyField('Varianty', through='PoptavkaVarianty')

    def __str__(self):
        return f"Poptávka #{self.id} u dodavatele: {self.dodavatel.dodavatel}"
    

class PoptavkaVarianty(models.Model):   
    """
    Propojovací model mezi poptávkami a variantami.

    Pole:
    - poptavka: Odkaz na poptávku (cizí klíč na model Poptavky).
    - varianta: Odkaz na variantu (cizí klíč na model Varianty).
    - mnozstvi: Množství poptávané varianty.
    - jednotky: Jednotky, ve kterých je množství měřeno (např. ks, kg).

    Meta:
    - verbose_name_plural: Množné číslo názvu modelu je "Poptávky variant".
    """
    poptavka = models.ForeignKey(Poptavky, on_delete=models.CASCADE, related_name='poptavka', verbose_name="Poptávka")
    varianta = models.ForeignKey(Varianty, on_delete=models.CASCADE, related_name='varianta', verbose_name="Varianta")
    mnozstvi = models.PositiveIntegerField(verbose_name="Množství")
    jednotky = models.CharField(max_length=10, choices=JEDNOTKY_CHOICES, verbose_name="Jednotky")

    def __str__(self):
        return f"{self.poptavka} - {self.varianta} - {self.mnozstvi} {self.jednotky}"