from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User

from .models import Poptavky, Dodavatele, Sklad, Zarizeni, AuditLog, Varianty, PoptavkaVarianty

######################## Testy Modelů ###########################

class SkladModelTest(TestCase):

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

    def setUp(self):
        self.zarizeni = Zarizeni.objects.create(
            zarizeni='Z001',
            nazev_zarizeni='Test Zařízení',
            umisteni='Sklad B',
            typ_zarizeni='Typ 1'
        )

    def test_zarizeni_creation(self):
        self.assertTrue(isinstance(self.zarizeni, Zarizeni))
        self.assertEqual(str(self.zarizeni), 'Z001')


class AuditLogModelTest(TestCase):

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

    def test_valid_zarizeni(self):
        zarizeni = Zarizeni(
            zarizeni='Z001',
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
            zarizeni='Z001',
            umisteni='Sklad B',
            typ_zarizeni='Typ 1'
        )
        with self.assertRaises(ValidationError):
            zarizeni.full_clean()  # Should raise a ValidationError due to missing nazev_zarizeni


class AuditLogModelValidationTest(TestCase):

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


####### Test pro vztahy mezi modely (Foreign Key a ManyToMany) #####

class SkladForeignKeyTest(TestCase):

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


######################## Testy View ###########################
class PoptavkaDetailViewTest(TestCase):
    def setUp(self):
        # Vytvoření uživatele pro přihlášení
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Vytvoření příkladu modelu Dodavatele
        self.dodavatel = Dodavatele.objects.create(
            dodavatel='Test Dodavatel',
            kontakt='Test Kontakt',
            email='test@example.com',
            telefon='123456789',
            jazyk='CZ'
        )

        # Vytvoření příkladu modelu Poptavky
        self.poptavka = Poptavky.objects.create(
            dodavatel=self.dodavatel,
            stav='Tvorba'
        )

        # URL pro testování detailního pohledu
        self.url = reverse('detail_poptavky', kwargs={'pk': self.poptavka.pk})

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_view_uses_correct_template(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hpm_sklad/detail_poptavky.html')

    def test_context_data(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('detail_item_fields', response.context)
        detail_item_fields = response.context['detail_item_fields']
        self.assertTrue(len(detail_item_fields) > 0)  # Ověříme, že tam nějaká pole jsou

    def test_poptavky_stav_choices(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        stav_field = self.poptavka._meta.get_field('stav')
        self.assertEqual(stav_field.choices, [
            ('Tvorba', 'Ve tvorbě'),
            ('Poptáno', 'Poptáno'),
            ('Uzavřeno', 'Uzavřeno')
        ])
        self.assertEqual(self.poptavka.stav, 'Tvorba')
