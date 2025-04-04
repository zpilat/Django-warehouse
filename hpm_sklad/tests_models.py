from django.test import TestCase
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_user_agents.utils import get_user_agent

from datetime import date

from .models import Poptavky, Dodavatele, Sklad, Zarizeni, SkladZarizeni, AuditLog, Varianty, PoptavkaVarianty

######################## Testy Modelů ###########################

class SkladModelTest(TestCase):
    """
    Testuje základní funkce modelu Sklad.

    Testy:
    - test_sklad_creation: Ověřuje, že model Sklad je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    - test_get_absolute_url: Testuje, zda metoda get_absolute_url vrací správnou URL pro model Sklad.
    - test_pod_minimem_property: Testuje, zda vlastnost pod_minimem správně určuje, zda je množství pod minimální hranicí.
    - test_pod_minimem_display: Testuje, zda metoda pod_minimem_display vrací správný řetězec ("ANO" nebo "NE").
    """

    def setUp(self):
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            objednano='Ano',
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=10,
            mnozstvi=5,
            jednotky='ks',
            umisteni='Sklad A',
            dodavatel='Test Dodavatel',
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=500.0,
            poznamka='Poznámka k dílu',
            ucetnictvi=True,
            kriticky_dil=False
        )

    def test_sklad_creation(self):
        self.assertTrue(isinstance(self.sklad, Sklad))
        self.assertEqual(str(self.sklad), f"Evid. č. {self.sklad.evidencni_cislo}, Testovací díl")

    def test_get_absolute_url(self):
        self.assertEqual(self.sklad.get_absolute_url(), reverse("sklad"))

    def test_pod_minimem_property(self):
        self.assertTrue(self.sklad.pod_minimem)

    def test_pod_minimem_display(self):
        self.assertEqual(self.sklad.pod_minimem_display(), "ANO")


class DodavateleModelTest(TestCase):
    """
    Testuje základní funkce modelu Dodavatele.

    Testy:
    - test_dodavatel_creation: Ověřuje, že model Dodavatele je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel',
            kontakt='Test Kontakt',
            email='test@example.com',
            telefon='123456789',
            jazyk='CZ'
        )

    def test_dodavatel_creation(self):
        self.assertTrue(isinstance(self.dodavatel, Dodavatele))
        self.assertEqual(str(self.dodavatel), 'Test Dodavatel')

 
class ZarizeniModelTest(TestCase):
    """
    Testuje základní funkce modelu Zarizeni.

    Testy:
    - test_zarizeni_creation: Ověřuje, že model Zarizeni je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.zarizeni = Zarizeni.objects.create(
            kod_zarizeni='Z001',
            nazev_zarizeni='Ipsen W',
            umisteni='Sklad B',
            typ_zarizeni='Pračka'
        )

    def test_zarizeni_creation(self):
        self.assertTrue(isinstance(self.zarizeni, Zarizeni))
        self.assertEqual(str(self.zarizeni), 'Ipsen W')


class AuditLogModelTest(TestCase):
    """
    Testuje základní funkce modelu AuditLog.

    Testy:
    - test_audit_log_creation: Ověřuje, že model AuditLog je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.audit_log = AuditLog.objects.create(
            ucetnictvi=True,
            evidencni_cislo=self.sklad,
            interne_cislo=self.sklad.interne_cislo,
            nazev_dilu=self.sklad.nazev_dilu,
            zmena_mnozstvi=5,
            mnozstvi=10,
            jednotky='ks',
            typ_operace='PŘÍJEM',
            dodavatel='Test Dodavatel',
            operaci_provedl=self.user
        )

    def test_audit_log_creation(self):
        self.assertTrue(isinstance(self.audit_log, AuditLog))
        self.assertEqual(str(self.audit_log), 'PŘÍJEM: 5x Testovací díl')

class VariantyModelTest(TestCase):
    """
    Testuje základní funkce modelu Varianty.

    Testy:
    - test_varianta_creation: Ověřuje, že model Varianty je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )
        self.varianta = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )

    def test_varianta_creation(self):
        self.assertTrue(isinstance(self.varianta, Varianty))
        self.assertEqual(str(self.varianta), 'Varianta A')

class PoptavkyModelTest(TestCase):
    """
    Testuje základní funkce modelu Poptavky.

    Testy:
    - test_poptavka_creation: Ověřuje, že model Poptavky je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )
        self.poptavka = Poptavky.objects.create(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )

    def test_poptavka_creation(self):
        self.assertTrue(isinstance(self.poptavka, Poptavky))
        self.assertEqual(str(self.poptavka), f"Poptávka #{self.poptavka.id} u dodavatele: Test Dodavatel")

class PoptavkaVariantyModelTest(TestCase):
    """
    Testuje základní funkce modelu PoptavkaVarianty.

    Testy:
    - test_poptavka_varianta_creation: Ověřuje, že model PoptavkaVarianty je správně vytvořen a jeho stringová reprezentace odpovídá očekávání.
    """

    def setUp(self):
        self.dodavatel = Dodavatele.objects.create(dodavatel='Test Dodavatel')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.varianta = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100            
        )
        self.poptavka = Poptavky.objects.create(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )
        self.poptavka_varianta = PoptavkaVarianty.objects.create(
            poptavka=self.poptavka,
            varianta=self.varianta,
            mnozstvi=100,
            jednotky='ks'
        )

    def test_poptavka_varianta_creation(self):
        self.assertTrue(isinstance(self.poptavka_varianta, PoptavkaVarianty))
        self.assertEqual(str(self.poptavka_varianta), f"{self.poptavka} - {self.varianta} - 100 ks")


######################## Testy validace dat modelů ############
 
class SkladModelValidationTest(TestCase):
    """
    Testuje validaci modelu Sklad.

    Testy:
    - test_valid_sklad: Ověřuje, že platná data nevyvolají chybu validace.
    - test_negative_mnozstvi: Ověřuje, že záporné množství vyvolá chybu validace.
    - test_invalid_jednotky_choice: Ověřuje, že neplatná volba pro jednotky vyvolá chybu validace.
    - test_negative_jednotkova_cena: Ověřuje, že záporná cena vyvolá chybu validace.
    """

    def test_valid_sklad(self):
        sklad = Sklad(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=10,
            mnozstvi=5,
            jednotky='ks',
            umisteni='Sklad A',            
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=500.0
        )
        try:
            sklad.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("Sklad model validation failed for valid data.")

    def test_negative_mnozstvi(self):
        sklad = Sklad(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=10,
            mnozstvi=-5,  # Invalid negative quantity
            jednotky='ks',
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=500.0
        )
        with self.assertRaises(ValidationError):
            sklad.full_clean()  # Should raise a ValidationError due to negative mnozstvi

    def test_invalid_jednotky_choice(self):
        sklad = Sklad(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=10,
            mnozstvi=5,
            jednotky='invalid_choice',  # Invalid choice
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=500.0
        )
        with self.assertRaises(ValidationError):
            sklad.full_clean()  # Should raise a ValidationError due to invalid jednotky choice

    def test_negative_jednotkova_cena(self):
        sklad = Sklad(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=10,
            mnozstvi=5,
            jednotky='ks',
            jednotkova_cena_eur=-100.0,  # Invalid negative price
            celkova_cena_eur=500.0
        )
        with self.assertRaises(ValidationError):
            sklad.full_clean()  # Should raise a ValidationError due to negative jednotkova_cena_eur


class DodavateleModelValidationTest(TestCase):
    """
    Testuje validaci modelu Dodavatele.

    Testy:
    - test_valid_dodavatel: Ověřuje, že platná data nevyvolají chybu validace.
    - test_invalid_email: Ověřuje, že neplatný e-mail vyvolá chybu validace.
    - test_invalid_jazyk_choice: Ověřuje, že neplatná volba pro jazyk vyvolá chybu validace.
    """

    def test_valid_dodavatel(self):
        dodavatel = Dodavatele(
            dodavatel='Test Dodavatel',
            kontakt='Test Kontakt',
            email='test@example.com',
            telefon='123456789',
            jazyk='CZ'
        )
        try:
            dodavatel.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("Dodavatele model validation failed for valid data.")

    def test_invalid_email(self):
        dodavatel = Dodavatele(
            dodavatel='Test Dodavatel',
            kontakt='Test Kontakt',
            email='invalid-email',  # Invalid email format
            telefon='123456789',
            jazyk='CZ'
        )
        with self.assertRaises(ValidationError):
            dodavatel.full_clean()  # Should raise a ValidationError due to invalid email

    def test_invalid_jazyk_choice(self):
        dodavatel = Dodavatele(
            dodavatel='Test Dodavatel',
            kontakt='Test Kontakt',
            email='test@example.com',
            telefon='123456789',
            jazyk='invalid_choice'  # Invalid language choice
        )
        with self.assertRaises(ValidationError):
            dodavatel.full_clean()  # Should raise a ValidationError due to invalid jazyk choice


class ZarizeniModelValidationTest(TestCase):
    """
    Testuje validaci modelu Zarizeni.

    Testy:
    - test_valid_zarizeni: Ověřuje, že platná data nevyvolají chybu validace.
    - test_missing_nazev_zarizeni: Ověřuje, že chybějící název zařízení vyvolá chybu validace.
    """

    def test_valid_zarizeni(self):
        zarizeni = Zarizeni(
            kod_zarizeni='Z001',
            nazev_zarizeni='Test Zařízení',
            umisteni='Sklad B',
            typ_zarizeni='Typ 1'
        )

        try:
            zarizeni.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("Zarizeni model validation failed for valid data.")

    def test_missing_nazev_zarizeni(self):
        zarizeni = Zarizeni(
            kod_zarizeni='Z001',
            umisteni='Sklad B',
            typ_zarizeni='Typ 1'
        )

        with self.assertRaises(ValidationError):
            zarizeni.full_clean()  # Should raise a ValidationError due to missing nazev_zarizeni


class AuditLogModelValidationTest(TestCase):
    """
    Testuje validaci modelu Varianty.

    Testy:
    - test_valid_varianta: Ověřuje, že platná data nevyvolají chybu validace.
    - test_negative_jednotkova_cena: Ověřuje, že záporná jednotková cena vyvolá chybu validace.
    """

    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )

    def test_valid_audit_log(self):
        audit_log = AuditLog(
            ucetnictvi=True,
            evidencni_cislo=self.sklad,
            interne_cislo=self.sklad.interne_cislo,
            nazev_dilu=self.sklad.nazev_dilu,
            zmena_mnozstvi=5,
            mnozstvi=10,
            jednotky='ks',
            typ_operace='PŘÍJEM',
            pouzite_zarizeni='Zařízení 1',
            umisteni='Sklad A',            
            dodavatel='Test Dodavatel',
            typ_udrzby='Preventivní', 
            operaci_provedl=self.user
        )
        try:
            audit_log.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("AuditLog model validation failed for valid data.")

    def test_invalid_movement_choice(self):
        audit_log = AuditLog(
            ucetnictvi=True,
            evidencni_cislo=self.sklad,
            interne_cislo=self.sklad.interne_cislo,
            nazev_dilu=self.sklad.nazev_dilu,
            zmena_mnozstvi=5,
            mnozstvi=10,
            jednotky='ks',
            typ_operace='INVALID',  # Invalid movement type
            dodavatel='Test Dodavatel',
            operaci_provedl=self.user
        )
        with self.assertRaises(ValidationError):
            audit_log.full_clean()  # Should raise a ValidationError due to invalid typ_operace choic


class VariantyModelValidationTest(TestCase):
    """
    Testuje validaci modelu Poptavky.

    Testy:
    - test_valid_poptavka: Ověřuje, že platná data nevyvolají chybu validace.
    - test_invalid_stav_choice: Ověřuje, že neplatná volba pro stav vyvolá chybu validace.
    """

    def setUp(self):
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )

    def test_valid_varianta(self):
        varianta = Varianty(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            cislo_varianty = "Číslo varianty",
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )
        try:
            varianta.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("Varianty model validation failed for valid data.")

    def test_negative_jednotkova_cena(self):
        varianta = Varianty(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            jednotkova_cena_eur=-10.0,  # Invalid negative price
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )
        with self.assertRaises(ValidationError):
            varianta.full_clean()  # Should raise a ValidationError due to negative jednotkova_cena_eur


class PoptavkyModelValidationTest(TestCase):
    """
    Testuje validaci modelu Poptavky.

    Testy:
    - test_valid_poptavka: Ověřuje, že platná data nevyvolají chybu validace.
    - test_invalid_stav_choice: Ověřuje, že neplatná volba pro stav vyvolá chybu validace.
    """

    def setUp(self):
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )

    def test_valid_poptavka(self):
        poptavka = Poptavky(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )
        try:
            poptavka.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("Poptavky model validation failed for valid data.")

    def test_invalid_stav_choice(self):
        poptavka = Poptavky(
            dodavatel=self.dodavatel,
            stav='INVALID'  # Invalid stav choice
        )
        with self.assertRaises(ValidationError):
            poptavka.full_clean()  # Should raise a ValidationError due to invalid stav choice


class PoptavkaVariantyModelValidationTest(TestCase):
    """
    Testuje validaci modelu PoptavkaVarianty.

    Testy:
    - test_valid_poptavka_varianta: Ověřuje, že platná data nevyvolají chybu validace.
    - test_invalid_jednotky_choice: Ověřuje, že neplatná volba pro jednotky vyvolá chybu validace.
    """

    def setUp(self):
        self.dodavatel = Dodavatele.objects.create(dodavatel='Test Dodavatel')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.varianta = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            cislo_varianty = "Číslo varianty",
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100            
        )
        self.poptavka = Poptavky.objects.create(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )

    def test_valid_poptavka_varianta(self):
        poptavka_varianta = PoptavkaVarianty(
            poptavka=self.poptavka,
            varianta=self.varianta,
            mnozstvi=100,
            jednotky='ks'
        )
        try:
            poptavka_varianta.full_clean()  # Should not raise a ValidationError
        except ValidationError:
            self.fail("PoptavkaVarianty model validation failed for valid data.")

    def test_invalid_jednotky_choice(self):
        poptavka_varianta = PoptavkaVarianty(
            poptavka=self.poptavka,
            varianta=self.varianta,
            mnozstvi=100,
            jednotky='invalid_choice'  # Invalid choice
        )
        with self.assertRaises(ValidationError):
            poptavka_varianta.full_clean()  # Should raise a ValidationError due to invalid jednotky choice


####### Testy pro vztahy mezi modely (Foreign Key a ManyToMany) #####

class SkladForeignKeyTest(TestCase):
    """
    Testuje vztahy mezi modelem Sklad a modelem Varianty přes ForeignKey.

    Testy:
    - test_sklad_varianta_relationship: Ověřuje, že skladová položka má přiřazené dvě varianty a tyto varianty jsou správně propojeny se skladovou položkou.
    """


    def setUp(self):
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )
        self.varianta1 = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta 1',
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )
        self.varianta2 = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta 2',
            jednotkova_cena_eur=15.0,
            dodaci_lhuta=10,
            min_obj_mnozstvi=50
        )

    def test_sklad_varianta_relationship(self):
        self.assertEqual(self.sklad.varianty_skladu.count(), 2)
        self.assertIn(self.varianta1, self.sklad.varianty_skladu.all())
        self.assertIn(self.varianta2, self.sklad.varianty_skladu.all())


class AuditLogForeignKeyTest(TestCase):
    """
    Testuje vztah mezi modelem AuditLog a modelem Sklad přes ForeignKey.

    Testy:
    - test_audit_log_sklad_relationship: Ověřuje, že audit log je správně propojen s odpovídající skladovou položkou a že název dílu odpovídá názvu položky ve skladu.
    """

    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.audit_log = AuditLog.objects.create(
            ucetnictvi=True,
            evidencni_cislo=self.sklad,
            interne_cislo=self.sklad.interne_cislo,
            nazev_dilu=self.sklad.nazev_dilu,
            zmena_mnozstvi=5,
            mnozstvi=10,
            jednotky='ks',
            typ_operace='PŘÍJEM',
            dodavatel='Test Dodavatel',
            operaci_provedl=self.user
        )

    def test_audit_log_sklad_relationship(self):
        self.assertEqual(self.audit_log.evidencni_cislo, self.sklad)
        self.assertEqual(self.audit_log.evidencni_cislo.nazev_dilu, 'Testovací díl')


class VariantyForeignKeyTest(TestCase):
    """
    Testuje vztah mezi modelem Varianty a modelem Dodavatele přes ForeignKey.

    Testy:
    - test_varianta_dodavatel_relationship: Ověřuje, že varianta je správně propojena s odpovídajícím dodavatelem a že dodavatel odpovídá názvu "Test Dodavatel".
    """

    def setUp(self):
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )
        self.varianta = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )

    def test_varianta_dodavatel_relationship(self):
        self.assertEqual(self.varianta.dodavatel, self.dodavatel)
        self.assertEqual(self.varianta.dodavatel.dodavatel, 'Test Dodavatel')


class PoptavkyManyToManyTest(TestCase):
    """
    Testuje vztah mezi modely Poptavky a Varianty přes prostřední model PoptavkaVarianty (ManyToMany).

    Testy:
    - test_poptavka_varianta_relationship: Ověřuje, že daná varianta je správně propojena s poptávkou přes prostřední model a že poptávka existuje.
    - test_varianta_poptavka_relationship: Ověřuje, že daná poptávka má přiřazenou pouze jednu variantu přes prostřední model.
    - test_through_model: Ověřuje, že prostřední model PoptavkaVarianty správně propojuje variantu a poptávku a že přiřazené hodnoty (množství a jednotky) jsou správné.
    """

    def setUp(self):
        # Vytvoření objektů Sklad a Dodavatele
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl'
        )
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel'
        )
        
        # Vytvoření objektu Varianty
        self.varianta = Varianty.objects.create(
            sklad=self.sklad,
            dodavatel=self.dodavatel,
            nazev_varianty='Varianta A',
            cislo_varianty="Číslo varianty",
            jednotkova_cena_eur=10.0,
            dodaci_lhuta=7,
            min_obj_mnozstvi=100
        )
        
        # Vytvoření objektu Poptavky
        self.poptavka = Poptavky.objects.create(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )
        
        # Propojení Varianty a Poptavky přes prostřední model PoptavkaVarianty
        self.poptavka_varianta = PoptavkaVarianty.objects.create(
            poptavka=self.poptavka,
            varianta=self.varianta,
            mnozstvi=50,
            jednotky='ks'
        )

    def test_poptavka_varianta_relationship(self):
        # Získání všech poptávek, které obsahují danou variantu
        poptavky_for_varianta = Poptavky.objects.filter(poptavka__varianta=self.varianta)

        # Ověření, že existuje pouze jedna poptávka pro danou variantu
        self.assertEqual(poptavky_for_varianta.count(), 1)
        self.assertEqual(poptavky_for_varianta.first(), self.poptavka)

    def test_varianta_poptavka_relationship(self):
        # Získání všech variant pro danou poptávku
        varianty_for_poptavka = Varianty.objects.filter(varianta__poptavka=self.poptavka)

        # Ověření, že existuje pouze jedna varianta pro danou poptávku
        self.assertEqual(varianty_for_poptavka.count(), 1)
        self.assertEqual(varianty_for_poptavka.first(), self.varianta)

    def test_through_model(self):
        # Ověření, že prostřední model je správně propojen
        self.assertEqual(self.poptavka_varianta.poptavka, self.poptavka)
        self.assertEqual(self.poptavka_varianta.varianta, self.varianta)
        self.assertEqual(self.poptavka_varianta.mnozstvi, 50)
        self.assertEqual(self.poptavka_varianta.jednotky, 'ks')


class ZarizeniManyToManyTest(TestCase):
    """
    Testuje vztah mezi modely Sklad a Zarizeni přes prostřední model SkladZarizeni (ManyToMany).

    Testy:
    - test_skladovapolozka_zarizeni_relationship: Ověřuje, že dané zařízení je správně propojeno se skladovou položkou přes prostřední model a že skladová položka existuje.
    - test_varianta_poptavka_relationship: Ověřuje, že daná skladová položka má přiřazenou pouze jedno zařízení přes prostřední model a že toto zařízení existuje.
    - test_through_model: Ověřuje, že prostřední model SkladZarizeni správně propojuje skladovou položku a zařízení.
    - test_unique_together: Ověřuje, že nelze vložit duplicitní záznam (kombinace sklad–zařízení) do mezitabulky SkladZarizeni.
    """

    def setUp(self):
        # Vytvoření skladové položky
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=5,
            mnozstvi=10,
            jednotky='ks',
            umisteni='Sklad A',
            jednotkova_cena_eur=50.0,
            celkova_cena_eur=500.0,
            ucetnictvi=True,
            kriticky_dil=False,
        )      

        # Vytvoření zařízení
        self.zarizeni = Zarizeni.objects.create(
            kod_zarizeni='hsh',	
            nazev_zarizeni='HSH TQ7',
            umisteni='Hala 1',
            typ_zarizeni='Víceúčelová kalicí pec'
        )
   
        # Propojení Sklad a Zařízení přes prostřední model SkladZarizeni
        self.sklad_zarizeni = SkladZarizeni.objects.create(
            sklad=self.sklad,
            zarizeni=self.zarizeni,
        )

    def test_skladovapolozka_zarizeni_relationship(self):
        # Získání všech skladových položek, které obsahují dané zařízení
        skladovepolozky_for_zarizeni = Sklad.objects.filter(zarizeni=self.zarizeni)

        # Ověření, že existuje pouze jedna skladová položka s daným zařízením
        self.assertEqual(skladovepolozky_for_zarizeni.count(), 1)
        self.assertEqual(skladovepolozky_for_zarizeni.first(), self.sklad)

    def test_zarizeni_skladovapolozka_relationship(self):
        # Získání všech zařízení pro danou skladovou položku
        zarizeni_for_skladovapolozka = Zarizeni.objects.filter(sklad=self.sklad)

        # Ověření, že existuje pouze jedno zarizeni pro danou skladovou položku
        self.assertEqual(zarizeni_for_skladovapolozka.count(), 1)
        self.assertEqual(zarizeni_for_skladovapolozka.first(), self.zarizeni)

    def test_through_model(self):
        # Ověření, že prostřední model je správně propojen
        self.assertEqual(self.sklad_zarizeni.sklad, self.sklad)
        self.assertEqual(self.sklad_zarizeni.zarizeni, self.zarizeni)

    def test_unique_together(self):
        # Ověření, že nelze vložit duplicitní záznam (kombinace sklad–zařízení) do mezitabulky SkladZarizeni.
        with self.assertRaises(IntegrityError):
            SkladZarizeni.objects.create(
                sklad=self.sklad,
                zarizeni=self.zarizeni,
            )    
