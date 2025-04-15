import csv
from io import StringIO, BytesIO

from django.test import TestCase, RequestFactory
from unittest.mock import patch
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django.contrib.auth.models import User, Permission

from django.core.files.uploadedfile import SimpleUploadedFile

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_user_agents.utils import get_user_agent
from django.http import FileResponse

from datetime import date

from hpm_sklad.models import Poptavky, Dodavatele, Sklad, Zarizeni, SkladZarizeni, AuditLog, Varianty, PoptavkaVarianty
from hpm_sklad.forms import SkladReceiptForm, AuditLogReceiptForm, SkladDispatchForm, AuditLogDispatchForm
from hpm_sklad.views import SkladListView, AuditLogListView, SkladCreateView, SkladUpdateView, SkladDeleteView, SkladDetailView


######################## Testy View ###########################

class HomeViewTest(TestCase):
    """
    Testy pro view `home_view`, které zobrazuje úvodní stránku aplikace.

    Testuje:
    - Přístupnost stránky bez nutnosti přihlášení.
    - Správné vykreslení šablony `home.html`.
    - Správné předání přihlášeného uživatele do kontextu.
    """

    def setUp(self):
        """
        Příprava testovacího prostředí:
        - Vytvoření uživatele pro testování přihlášeného stavu.
        - Nastavení URL pro testování.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('home')

    def test_home_view_accessible_without_login(self):
        """
        Ověřuje, že na úvodní stránku lze přistupovat bez nutnosti přihlášení.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_renders_correct_template(self):
        """
        Ověřuje, že view používá správnou šablonu `home.html`.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hpm_sklad/home.html')

    def test_home_view_context_for_logged_in_user(self):
        """
        Ověřuje, že přihlášený uživatel je správně předán do kontextu šablony.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_user'], self.user)

    def test_home_view_context_for_anonymous_user(self):
        """
        Ověřuje, že nepřihlášený uživatel je správně nastaven jako `AnonymousUser` v kontextu.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.context['current_user']), 'AnonymousUser')


class ReceiptFormViewTest(TestCase):
    """
    Testy pro view `receipt_form_view`, které zpracovává příjem položky na sklad.

    Funkce view testuje:
    - Přihlášení a oprávnění uživatele (login_required a permission_required).
    - Správné vykreslení šablony a kontextu při GET requestu.
    - Správné výpočty a aktualizaci jednotkové ceny a celkové ceny skladu při POST requestu.
    - Přesměrování na vytvoření nové varianty, pokud neexistuje varianta pro daného dodavatele.
    - Zápis správných dat do audit logu.
    - Edge case: Příjem položky na sklad s nulovým množstvím na skladě.
    - Správné chování při zadání neplatných dat ve formuláři (záporná množství, záporné ceny, neplatná data).
    - Správné chování při zadání budoucího data nákupu.
    - Ověření, že audit log ukládá všechna dodatečná pole správně.
    - Ověření, že formulář po chybě ve validaci zůstává vyplněný původními hodnotami.
    - Správné výpočty při příjmu velkého množství položek na sklad.
    - Ověření správné reakce na neplatný primární klíč (pk) - návratová hodnota 404.
    """

    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele s oprávněními `change_sklad` a `add_auditlog`.
        - Vytvoření skladové položky.
        - Vytvoření dodavatele.
        - Vytvoření URL pro testování.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='change_sklad'))
        self.user.user_permissions.add(Permission.objects.get(codename='add_auditlog'))

        self.dodavatel = Dodavatele.objects.create(dodavatel='Test Dodavatel')

        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            mnozstvi=10,
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=1000.0,
            dodavatel=self.dodavatel.dodavatel,
            umisteni = 'Sklad A',
            jednotky = 'ks',
        )

        self.url = reverse('receipt_audit_log', kwargs={'pk': self.sklad.pk})

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění dostane chybu 403.
        """
        self.client.login(username='testuser', password='testpassword')
        self.user.user_permissions.clear()  # Odebrání oprávnění
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_receipt_view_renders_correct_template(self):
        """
        Ověřuje, že view používá správnou šablonu `receipt_audit_log.html`.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hpm_sklad/receipt_audit_log.html')

    def test_valid_post_updates_sklad_and_audit_log(self):
        """
        Testuje, že POST request správně aktualizuje stav skladu a vytvoří záznam v audit logu.
        - Ověřuje správné výpočty jednotkové ceny, množství a celkové ceny.
        - Ověřuje záznam v audit logu.
        - Přesměrování na `audit_log` po úspěšném zpracování.
        """
        self.client.login(username='testuser', password='testpassword')

        self.varianta = Varianty.objects.create(
        sklad=self.sklad,  
        dodavatel=self.dodavatel,  
        nazev_varianty='Test Varianta', 
        jednotkova_cena_eur=50.0,
        dodaci_lhuta=5,
        min_obj_mnozstvi=2 
        )

        post_data = {
            'zmena_mnozstvi': 5,  # Příjem 5 kusů
            'datum_nakupu': '2024-10-01',
            'jednotkova_cena_eur': 120.0,  # Nová cena
            'dodavatel': self.dodavatel.pk,
            'umisteni': 'Sklad A',
            'cislo_objednavky': '12345',
            'poznamka': 'Testovací poznámka',
            'objednano': 100
        }

        response = self.client.post(self.url, data=post_data)

        sklad = Sklad.objects.get(pk=self.sklad.pk)
        self.assertEqual(sklad.mnozstvi, 15)  # Množství se zvýší
        self.assertAlmostEqual(sklad.jednotkova_cena_eur, 106.67, places=2)  # Zprůměrovaná cena
        self.assertAlmostEqual(sklad.celkova_cena_eur, 1600.0)  # Nová celková cena

        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.zmena_mnozstvi, 5)
        self.assertEqual(audit_log.jednotkova_cena_eur, 120.0)
        self.assertEqual(audit_log.typ_operace, "PŘÍJEM")
        self.assertEqual(audit_log.evidencni_cislo, sklad)

        self.assertRedirects(response, reverse('audit_log'))

    def test_new_variant_redirect(self):
        """
        Ověřuje přesměrování na vytvoření nové varianty, pokud pro dodavatele neexistuje varianta.
        """
        self.client.login(username='testuser', password='testpassword')
        Varianty.objects.filter(sklad=self.sklad).delete()

        post_data = {
            'zmena_mnozstvi': 10,  
            'datum_nakupu': '2024-10-01',
            'jednotkova_cena_eur': 50.0,
            'dodavatel': self.dodavatel.pk,
            'umisteni': 'Sklad A',
            'cislo_objednavky': '12345',
            'poznamka': 'Testovací poznámka',
            'objednano': 100
        }
        response = self.client.post(self.url, data=post_data)

        self.assertRedirects(response, reverse('create_varianty_with_dodavatel', kwargs={'pk': self.sklad.pk, 'dodavatel': self.dodavatel.pk}))

    def test_context_data(self):
        """
        Ověřuje, že view vrací správná data v kontextu.
        - Ověřuje přítomnost formulářů v kontextu.
        - Ověřuje, že v kontextu je správná položka skladu.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['sklad_movement_form'], SkladReceiptForm)
        self.assertIsInstance(response.context['auditlog_receipt_form'], AuditLogReceiptForm)
        self.assertEqual(response.context['object'], self.sklad)

    def test_edge_case_zero_stock(self):
        """
        Ověřuje správné výpočty, když je na skladě nulové množství.
        """
        self.client.login(username='testuser', password='testpassword')

        # Nastavení skladové položky na nulové množství a ceny
        self.sklad.mnozstvi = 0
        self.sklad.jednotkova_cena_eur = 0.0
        self.sklad.celkova_cena_eur = 0.0
        self.sklad.save()

        post_data = {
            'zmena_mnozstvi': 10,  
            'datum_nakupu': '2024-10-01',
            'jednotkova_cena_eur': 50.0,
            'dodavatel': self.dodavatel.pk,
            'umisteni': 'Sklad A',
            'cislo_objednavky': '12345',
            'poznamka': 'Testovací poznámka',
            'objednano': 100
        }

        self.client.post(self.url, data=post_data)

        sklad = Sklad.objects.get(pk=self.sklad.pk)
        self.assertEqual(sklad.mnozstvi, 10)
        self.assertAlmostEqual(sklad.jednotkova_cena_eur, 50.0)
        self.assertAlmostEqual(sklad.celkova_cena_eur, 500.0)

        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.zmena_mnozstvi, 10)
        self.assertEqual(audit_log.jednotkova_cena_eur, 50.0)
        self.assertEqual(audit_log.typ_operace, "PŘÍJEM")
        self.assertEqual(audit_log.evidencni_cislo, sklad)

    def test_invalid_negative_quantity(self):
        """
        Ověřuje, že formulář vrací chybu při zadání záporného množství.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
            'zmena_mnozstvi': -5,  # Záporné množství
            'datum_nakupu': '2024-10-01',
            'jednotkova_cena_eur': 50.0,
            'dodavatel': self.dodavatel.dodavatel
        }
        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)  # Ověřte, že se stránka načetla správně
        self.assertIn('zmena_mnozstvi', response.context['auditlog_receipt_form'].errors)  # Ověřte, že je v chybách správné pole
        self.assertEqual(response.context['auditlog_receipt_form'].errors['zmena_mnozstvi'], ['Hodnota musí být větší nebo rovna 1.'])  # Ověřte, že zpráva je správná

    def test_form_repopulates_on_error(self):
        """
        Ověřuje, že formulář zůstane vyplněný, pokud dojde k chybě ve validaci.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
            'zmena_mnozstvi': 'invalid',  # Neplatná hodnota
            'datum_nakupu': '2024-10-01',
            'jednotkova_cena_eur': 50.0,
            'dodavatel': self.dodavatel.dodavatel
        }
        response = self.client.post(self.url, data=post_data)

        # Ověření, že formulář zůstává vyplněný
        self.assertEqual(response.context['sklad_movement_form']['datum_nakupu'].value(), '2024-10-01')
        self.assertEqual(response.context['sklad_movement_form']['jednotkova_cena_eur'].value(), '50.0')
        self.assertEqual(response.context['sklad_movement_form']['dodavatel'].value(), str(self.dodavatel.dodavatel))

    def test_invalid_pk_returns_404(self):
        """
        Ověřuje, že view vrací chybu 404, pokud je poskytnut neplatný pk.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('receipt_audit_log', kwargs={'pk': 9999}))  # Neexistující skladová položka
        self.assertEqual(response.status_code, 404)


class DispatchFormViewTest(TestCase):
    """
    Testy pro view `dispatch_form_view`, které zpracovává výdej položky ze skladu.

    Funkce view testuje:
    - Přihlášení a oprávnění uživatele (login_required a permission_required).
    - Správné vykreslení šablony a kontextu při GET requestu.
    - Správné výpočty a aktualizaci jednotkové ceny a celkové ceny skladu při POST requestu.
    - Správné snížení množství položek na skladě a zápis do audit logu.
    - Edge case: Výdej více položek, než je aktuální množství na skladě.
    - Správné chování při zadání neplatných dat ve formuláři (záporná množství, nesprávná data).
    - Ověření, že audit log ukládá všechna data správně.
    - Ověření, že formulář po chybě ve validaci zůstává vyplněný původními hodnotami.
    - Správné chování při zadání neplatného primárního klíče (pk).
    """

    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele s oprávněními `change_sklad` a `add_auditlog`.
        - Vytvoření dodavatele.
        - Vytvoření skladové položky.
        - Vytvoření zařízení.
        - Přiřazení zařízení k skladové položce.
        - Vytvoření URL pro testování.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='change_sklad'))
        self.user.user_permissions.add(Permission.objects.get(codename='add_auditlog'))

        self.dodavatel = Dodavatele.objects.create(dodavatel='Test Dodavatel')

        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            mnozstvi=10,
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=1000.0,
            dodavatel=self.dodavatel.dodavatel
        )

        self.zarizeni = Zarizeni.objects.create(
            kod_zarizeni='hsh',	
            nazev_zarizeni='HSH TQ7',
            umisteni='Hala 1',
            typ_zarizeni='Víceúčelová kalicí pec'
        )

        self.sklad.zarizeni.add(self.zarizeni)

        self.url = reverse('dispatch_audit_log', kwargs={'pk': self.sklad.pk})

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění dostane chybu 403.
        """
        self.client.login(username='testuser', password='testpassword')
        self.user.user_permissions.clear()  # Odebrání oprávnění
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_dispatch_view_renders_correct_template(self):
        """
        Ověřuje, že view používá správnou šablonu `dispatch_audit_log.html`.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hpm_sklad/dispatch_audit_log.html')

    def test_valid_post_updates_sklad_and_audit_log(self):
        """
        Testuje, že POST request správně aktualizuje stav skladu a vytvoří záznam v audit logu.
        - Ověřuje správné výpočty jednotkové ceny, množství a celkové ceny při výdeji.
        - Ověřuje záznam v audit logu.
        - Přesměrování na `audit_log` po úspěšném zpracování.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
        'umisteni': 'Sklad A',  # Přidej umístění
        'poznamka': 'Výdej zboží',  # Přidej poznámku
        'zmena_mnozstvi': 5,  # Výdej 5 kusů
        'datum_vydeje': '2024-10-01',
        'typ_udrzby': 'Preventivní',
        'pouzite_zarizeni': "HSH",
        }
        response = self.client.post(self.url, data=post_data)

        sklad = Sklad.objects.get(pk=self.sklad.pk)
        self.assertEqual(sklad.mnozstvi, 5)  # Množství se sníží
        self.assertAlmostEqual(sklad.celkova_cena_eur, 500.0)  # Cena se sníží

        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.zmena_mnozstvi, -5)
        self.assertEqual(audit_log.jednotkova_cena_eur, 100.0)
        self.assertEqual(audit_log.typ_operace, "VÝDEJ")
        self.assertEqual(audit_log.evidencni_cislo, sklad)

        self.assertRedirects(response, reverse('audit_log'))

    def test_edge_case_more_than_stock(self):
        """
        Ověřuje správné chování, když se pokusíme vydat více položek, než je na skladě.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
            'umisteni': 'Sklad A',  # Přidej umístění
            'poznamka': 'Výdej zboží',  # Přidej poznámku
            'zmena_mnozstvi': 20,  # Výdej více než dostupné množství
            'datum_vydeje': '2024-10-01',
            'pouzite_zarizeni': "HSH",
        }
        response = self.client.post(self.url, data=post_data)

        # Kontrola, zda stránka vrací správný stavový kód a formulář obsahuje chybu
        self.assertEqual(response.status_code, 200)

        # Zkontroluj, že formulář zobrazuje chybu pro pole zmena_mnozstvi
        self.assertEqual(response.context['auditlog_dispatch_form'].errors['zmena_mnozstvi'], ['Vyberte platnou možnost, "20" není k dispozici.'])

    def test_invalid_negative_quantity(self):
        """
        Ověřuje, že formulář vrací chybu při zadání záporného množství.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
            'zmena_mnozstvi': -5,  # Záporné množství
            'datum_vydeje': '2024-10-01',
            'pouzite_zarizeni': "HSH",
        }
        response = self.client.post(self.url, data=post_data)

        # Ověření, že odpověď má status 200 (stránka byla vykreslena znovu s chybami)
        self.assertEqual(response.status_code, 200)

        # Ověření, že formulář vrátil očekávanou chybu v češtině
        self.assertEqual(
            response.context['auditlog_dispatch_form'].errors['zmena_mnozstvi'],
            ['Vyberte platnou možnost, "-5" není k dispozici.']  
        )

    def test_invalid_post_repopulates_form(self):
        """
        Ověřuje, že formulář zůstává vyplněný původními hodnotami, pokud dojde k chybě ve validaci.
        """
        self.client.login(username='testuser', password='testpassword')

        post_data = {
            'zmena_mnozstvi': 'invalid',  # Neplatná hodnota
            'datum_vydeje': '2024-10-01',
            'pouzite_zarizeni': 'Testovací zařízení'
        }
        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['auditlog_dispatch_form']['datum_vydeje'].value(), '2024-10-01')
        self.assertEqual(response.context['auditlog_dispatch_form']['pouzite_zarizeni'].value(), 'Testovací zařízení')

    def test_context_data(self):
        """
        Ověřuje, že view vrací správný kontext.
        - Ověřuje přítomnost formulářů v kontextu.
        - Ověřuje, že v kontextu je správná položka skladu.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['sklad_movement_form'], SkladDispatchForm)
        self.assertIsInstance(response.context['auditlog_dispatch_form'], AuditLogDispatchForm)
        self.assertEqual(response.context['object'], self.sklad)

    def test_invalid_pk_returns_404(self):
        """
        Ověřuje, že view vrací chybu 404, pokud je poskytnut neplatný pk.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('dispatch_audit_log', kwargs={'pk': 9999}))  # Neexistující skladová položka
        self.assertEqual(response.status_code, 404)


class SkladListViewTest(TestCase):
    """
    Testovací třída pro `SkladListView`, která ověřuje funkčnost seznamu skladových položek.

    Testuje následující scénáře:
    -----------------------------
    - Přístup k view vyžaduje přihlášení.
    - View používá správnou šablonu.
    - Filtrování podle názvu dílu a dalších parametrů funguje správně.
    - Stránkování funguje správně a zobrazuje maximálně 20 položek na stránce.
    - Export do CSV vrací správný formát a data.
    - Řazení položek skladu podle zadaných kritérií.
    - Kontrola vybrané položky skladu pomocí parametru `selected` v GET požadavku.
    """

    def setUp(self):
        # Vytvoření uživatele
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        url = reverse('sklad')
        response = self.client.get(url)
        self.assertRedirects(response, f'/account/login/?next={url}')

    def test_logged_in_user_can_access(self):
        """
        Ověřuje, že přihlášený uživatel má přístup k view.
        """
        self.client.login(username='testuser', password='testpassword')
        url = reverse('sklad')
        pc_user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/92.0.4515.131 Safari/537.36')
        response = self.client.get(url, HTTP_USER_AGENT=pc_user_agent)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hpm_sklad/sklad.html')

    def test_filtering_and_sorting(self):
        """
        Ověřuje správné filtrování a řazení položek skladu.
        """
        # Vytvoření testovacích položek ve skladu
        Sklad.objects.create(interne_cislo=100, nazev_dilu="Test1", mnozstvi=10)
        Sklad.objects.create(interne_cislo=101, nazev_dilu="Test2", mnozstvi=5)

        self.client.login(username='testuser', password='testpassword')
        url = reverse('sklad')

        # Test filtrování podle názvu dílu
        response = self.client.get(url, {'query': 'Test1'})
        self.assertContains(response, 'Test1')
        self.assertNotContains(response, 'Test2')

        # Test řazení podle množství vzestupně
        response = self.client.get(url, {'sort': 'mnozstvi', 'order': 'up'})
        sklad_items = response.context['object_list']
        self.assertEqual(sklad_items[0].nazev_dilu, 'Test2')
        self.assertEqual(sklad_items[1].nazev_dilu, 'Test1')

    def test_pagination(self):
        """
        Ověřuje správné stránkování.
        """
        # Vytvoření více než 24 položek
        for i in range(29):
            Sklad.objects.create(interne_cislo=i, nazev_dilu=f"Test{i}", mnozstvi=10)

        self.client.login(username='testuser', password='testpassword')
        url = reverse('sklad')
        pc_user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/92.0.4515.131 Safari/537.36')        

        # Zkontrolujeme, že je zobrazeno pouze 24 položek na první stránce
        response = self.client.get(url, HTTP_USER_AGENT=pc_user_agent)
        sklad_items = response.context['object_list']
        self.assertEqual(len(sklad_items), 24)

        # Ověříme, že na druhé stránce je zbývajících 5 položek
        response = self.client.get(url, {'page': 2}, HTTP_USER_AGENT=pc_user_agent)
        sklad_items = response.context['object_list']
        self.assertEqual(len(sklad_items), 5)

    def test_export_to_csv(self):
        """
        Ověřuje správný export do CSV bez úpravy view.
        """
        self.client.login(username='testuser', password='testpassword')
        url = reverse('sklad')

        # Vytvoření testovací položky ve skladu
        Sklad.objects.create(
            evidencni_cislo='12345',
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            mnozstvi=10,
            jednotkova_cena_eur=100.0,
            celkova_cena_eur=1000.0,
            umisteni='Sklad A',
            dodavatel='Test Dodavatel',
            cislo_objednavky='2024-001',
        )

        # Mockuje `render_to_response` metodu, aby byl export aktivován
        with patch.object(SkladListView, 'export_csv', True):
            response = self.client.get(url)

        # Ověř, že response je CSV formát
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="sklad_export.csv"')

        # Kontrola obsahu CSV
        content = response.content.decode('utf-8')
        lines = content.splitlines()
        
        # Ověř, že první řádek je záhlaví
        self.assertTrue(lines[0].startswith('Evidenční číslo'))

        # Ověř, že druhý řádek obsahuje data testovací položky
        self.assertIn('12345', lines[1])
        self.assertIn('Testovací díl', lines[1])
        self.assertIn('10', lines[1])  # Množství
        self.assertIn('100.0', lines[1])  # Jednotková cena EUR


class SkladCreateViewTest(TestCase):
    """
    Testy pro SkladCreateView:
    
    - Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
    - Ověřuje, že uživatel bez oprávnění 'add_sklad' dostane chybu 403.
    - Ověřuje, že přihlášený uživatel s oprávněním může vytvořit novou položku.
    """
    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele a přiřazení oprávnění.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='add_sklad'))
        self.client.login(username='testuser', password='testpassword')
        self.url = reverse('create_sklad')

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění 'add_sklad' dostane chybu 403.
        """
        self.user.user_permissions.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_sklad(self):
        """
        Ověřuje, že přihlášený uživatel s oprávněním může vytvořit novou položku ve skladu.
        """
        # Nejprve vytvořte jednu skladovou položku, aby bylo možné ji použít jako vybraný sklad (pk)
        existing_sklad = Sklad.objects.create(
            nazev_dilu='Předchozí díl',
            min_mnozstvi_ks=2,
            mnozstvi=5,
            jednotky='ks',
            umisteni='Sklad B',
            jednotkova_cena_eur=30.0,
            celkova_cena_eur=150.0
        )

        # URL pro vytvoření nové položky s parametrem pk z existující položky
        create_url_with_pk = f"{self.url}?pk={existing_sklad.pk}"
        
        # Data pro vytvoření nové položky
        post_data = {
            'interne_cislo': 123,  
            'nazev_dilu': 'Nový díl',
            'min_mnozstvi_ks': 5,
            'mnozstvi': 10,
            'jednotky': 'ks',  
            'umisteni': 'Sklad A',
            'jednotkova_cena_eur': 50.0,
            'celkova_cena_eur': 500.0,
        }

        # Odeslání POST požadavku s parametrem pk
        response = self.client.post(create_url_with_pk, post_data)
        
        # Ověření, že došlo k přesměrování na seznam skladů
        self.assertRedirects(response, reverse('sklad'))

        # Ověření, že nová položka byla vytvořena
        self.assertTrue(Sklad.objects.filter(nazev_dilu='Nový díl').exists())


class SkladUpdateViewTest(TestCase):
    """
    Testy pro SkladUpdateView:
    
    - Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
    - Ověřuje, že uživatel bez oprávnění 'change_sklad' dostane chybu 403.
    - Ověřuje, že přihlášený uživatel s oprávněním může aktualizovat položku.
    """
    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele, položky ve skladu a přiřazení oprávnění.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='change_sklad'))
        self.client.login(username='testuser', password='testpassword')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=5,
            mnozstvi=10,
            jednotky='ks',
            umisteni='Sklad A',
            jednotkova_cena_eur=50.0,
            celkova_cena_eur=500.0
        )
        self.url = reverse('update_sklad', kwargs={'pk': self.sklad.pk})

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění 'change_sklad' dostane chybu 403.
        """
        self.user.user_permissions.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_update_sklad(self):
        """
        Ověřuje, že přihlášený uživatel s oprávněním může aktualizovat položku ve skladu.
        """
        post_data = {
            'interne_cislo': 124,
            'min_mnozstvi_ks': 3,
            'nazev_dilu': 'Aktualizovaný díl',
            'jednotky': 'ks',
            'umisteni': 'Sklad B',
            'poznamka': 'Změněná poznámka',
            'ucetnictvi': True,
            'kriticky_dil': False,
        }

        # Odeslání POST požadavku s aktualizovanými daty
        response = self.client.post(self.url, post_data)

        # Ověření přesměrování po úspěšné aktualizaci
        self.assertRedirects(response, reverse('sklad'))

        # Ověření, že se položka správně aktualizovala
        self.sklad.refresh_from_db()
        self.assertEqual(self.sklad.interne_cislo, 124)
        self.assertEqual(self.sklad.nazev_dilu, 'Aktualizovaný díl')
        self.assertEqual(self.sklad.umisteni, 'Sklad B')
        self.assertEqual(self.sklad.poznamka, 'Změněná poznámka')
        self.assertTrue(self.sklad.ucetnictvi)
        self.assertFalse(self.sklad.kriticky_dil)


class SkladUpdateObjednanoViewTest(TestCase):
    """
    Testy pro SkladUpdateObjednanoView:

    - Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.    
    - Ověřuje, že uživatel bez oprávnění 'change_objednano_in_sklad' dostane chybu 403.
    - Ověřuje, že přihlášený uživatel s oprávnění může aktualizovat stav 'objednáno' u skladové položky.
    """
    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele a položky ve skladu.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='change_objednano_in_sklad'))        
        self.client.login(username='testuser', password='testpassword')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=5,
            mnozstvi=10,
            jednotky='ks',
            umisteni='Sklad A',
            jednotkova_cena_eur=50.0,
            celkova_cena_eur=500.0,
            objednano='Není'
        )
        self.url = reverse('update_objednano_sklad', kwargs={'pk': self.sklad.pk})

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')     

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění 'change_objednano_in_sklad' dostane chybu 403.
        """
        self.user.user_permissions.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)           

    def test_update_objednano(self):
        """
        Ověřuje, že přihlášený uživatel s oprávněním může aktualizovat stav 'objednáno' u skladové položky.
        """
        post_data = {
            'objednano': 'Už je objednáno'
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, reverse('sklad'))
        self.sklad.refresh_from_db()
        self.assertEqual(self.sklad.objednano, 'Už je objednáno')


class SkladDeleteViewTest(TestCase):
    """
    Testy pro SkladDeleteView:
    
    - Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
    - Ověřuje, že uživatel bez oprávnění 'delete_sklad' dostane chybu 403.
    - Ověřuje, že přihlášený uživatel s oprávněním může smazat položku ze skladu.
    """
    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele, položky ve skladu a přiřazení oprávnění.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.user_permissions.add(Permission.objects.get(codename='delete_sklad'))
        self.client.login(username='testuser', password='testpassword')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Testovací díl',
            min_mnozstvi_ks=5,
            mnozstvi=10,
            jednotky='ks',
            umisteni='Sklad A',
            jednotkova_cena_eur=50.0,
            celkova_cena_eur=500.0,
        )
        self.url = reverse('delete_sklad', kwargs={'pk': self.sklad.pk})

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_permission_required(self):
        """
        Ověřuje, že uživatel bez oprávnění 'delete_sklad' dostane chybu 403.
        """
        self.user.user_permissions.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_delete_sklad(self):
        """
        Ověřuje, že přihlášený uživatel s oprávněním může smazat položku ze skladu.
        """
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('sklad'))
        self.assertFalse(Sklad.objects.filter(pk=self.sklad.pk).exists())


class SkladDetailViewTest(TestCase):
    """
    Testy pro SkladDetailView:
    
    - Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
    - Ověřuje, že přihlášený uživatel může zobrazit detail skladové položky.
    - Ověřuje, že je použita správná šablona.
    - Ověřuje, že kontext obsahuje správné informace o skladové položce.
    """
    
    def setUp(self):
        """
        Nastavení testovacího prostředí:
        - Vytvoření uživatele a skladové položky.
        """
        # Vytvoření uživatele
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Vytvoření zařízení
        self.zarizeni = Zarizeni.objects.create(
            kod_zarizeni='hsh',	
            nazev_zarizeni='HSH TQ7',
            umisteni='Hala 1',
            typ_zarizeni='Víceúčelová kalicí pec'
        )

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

        # Přiřazení zařízení k položce skladu
        self.sklad.zarizeni.add(self.zarizeni)

        # URL pro detail položky
        self.url = reverse('detail_sklad', kwargs={'pk': self.sklad.pk})
    
    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na přihlašovací stránku.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')
    
    def test_detail_view_accessible_by_logged_in_user(self):
        """
        Ověřuje, že přihlášený uživatel může zobrazit detail skladové položky.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """
        Ověřuje, že správná šablona je použita pro zobrazení detailu skladové položky.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'hpm_sklad/detail_sklad.html')
    
    def test_context_contains_sklad_data(self):
        """
        Ověřuje, že kontext obsahuje správné informace o skladové položce.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)

        # Ověření přítomnosti skladové položky v kontextu
        sklad_item = response.context['object']
        self.assertEqual(sklad_item.nazev_dilu, 'Testovací díl')
        self.assertEqual(sklad_item.umisteni, 'Sklad A')
        self.assertEqual(sklad_item.mnozstvi, 10)

        # Ověření kontextových polí
        self.assertIn('equipment_fields', response.context)
        self.assertIn('info_fields', response.context)
        self.assertIn('detail_item_fields', response.context)
        self.assertIn('varianty', response.context)

        # Ověření přítomnosti polí zařízení, které jsou True
        equipment_fields = response.context['equipment_fields']
        self.assertIn(self.zarizeni.kod_zarizeni, equipment_fields)

        # Ověření, že pole pro informace jsou správně nastavená
        info_fields = response.context['info_fields']
        self.assertIn(Sklad._meta.get_field('ucetnictvi'), info_fields)
        self.assertIn(Sklad._meta.get_field('kriticky_dil'), info_fields)
        self.assertIn({'verbose_name': 'Pod minimem', 'name': 'pod_minimem'}, info_fields)


class AuditLogListViewTest(TestCase):
    """
    Testy pro AuditLogListView:
    - Ověření, že je přístup pouze pro přihlášené uživatele.
    - Správné použití šablony.
    - Filtrování podle dotazu, typu operace, typu údržby, roku a měsíce.
    - Stránkování (24 položek).
    - Kontrola vybraného záznamu.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.sklad = Sklad.objects.create(
            interne_cislo=123,
            nazev_dilu='Ložisko'
        )
        self.client.login(username='tester', password='testpass')


        # Vytvořím 29 záznamů v audit logu
        for i in range(29):
            AuditLog.objects.create(
                ucetnictvi=True,
                evidencni_cislo=self.sklad,
                interne_cislo=1000 + i,
                objednano='Ano',
                nazev_dilu='Ložisko' if i % 2 == 0 else 'Těsnění',
                zmena_mnozstvi=5,
                mnozstvi=10,
                jednotky='ks',
                typ_operace='VÝDEJ' if i % 2 == 0 else 'PŘÍJEM',
                pouzite_zarizeni='HSH',
                umisteni='Hala A',
                dodavatel='SKF',
                datum_vydeje=date(2024, 10, 1),
                datum_nakupu=date(2024, 10, 1),
                cislo_objednavky='OBJ123',
                jednotkova_cena_eur=10.0,
                celkova_cena_eur=50.0,
                operaci_provedl=self.user,
                typ_udrzby='Reaktivní',
                poznamka='Test'
            )

        self.url = reverse('audit_log')

    def test_login_required(self):
        """
        Ověřuje, že nepřihlášený uživatel je přesměrován na login.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/account/login/?next={self.url}')

    def test_template_used(self):
        """
        Ověřuje, že view používá správnou šablonu.
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'hpm_sklad/audit_log.html')

    def test_queryset_filtered_by_query(self):
        """
        Ověřuje filtrování podle dotazu `query`.
        """
        response = self.client.get(self.url, {'query': 'Ložisko'})
        self.assertTrue(all('Ložisko' in obj.nazev_dilu for obj in response.context['object_list']))

    def test_filter_by_typ_operace(self):
        """
        Ověřuje filtrování podle typu operace.
        """
        response = self.client.get(self.url, {'typ_operace': 'VÝDEJ'})
        self.assertTrue(all(obj.typ_operace == 'VÝDEJ' for obj in response.context['object_list']))

    def test_filter_by_typ_udrzby(self):
        """
        Ověřuje filtrování podle typu údržby.
        """
        response = self.client.get(self.url, {'typ_udrzby': 'Reaktivní'})
        self.assertTrue(all(obj.typ_udrzby == 'Reaktivní' for obj in response.context['object_list']))

    def test_pagination_is_24(self):
        """
        Ověřuje, že stránkování zobrazí 24 záznamů.
        """
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['object_list']), 24)

    def test_selected_context_variable(self):
        """
        Ověřuje, že parametr `selected` vrací vybraný objekt v kontextu.
        """
        obj = AuditLog.objects.first()
        response = self.client.get(self.url, {'selected': obj.id})
        self.assertEqual(response.context['selected_item'], obj)

    def test_filter_by_year_and_month(self):
        """
        Ověřuje filtrování podle měsíce a roku.
        """
        response = self.client.get(self.url, {'month': '10', 'year': '2024'})
        self.assertTrue(response.context['object_list'])


class AuditLogExportGraphTest(TestCase):
    """
    Testy pro metody exportu a generování grafů ve view AuditLogListView.

    Testuje:
    - Export do CSV vrací správná data.
    - Metody renderující grafy vracejí FileResponse.
    """

    def setUp(self):
        # Uživatelské přihlášení
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.client.login(username='tester', password='testpass')

        # Vytvoření skladové položky
        self.sklad = Sklad.objects.create(
            interne_cislo=100,
            nazev_dilu='Testovací díl',
            mnozstvi=5,
            jednotky='ks',
            jednotkova_cena_eur=10,
            celkova_cena_eur=50,
            ucetnictvi=True,
        )

        # Záznam v audit logu
        self.log = AuditLog.objects.create(
            ucetnictvi=True,
            evidencni_cislo=self.sklad,
            interne_cislo=100,
            objednano="ano",
            nazev_dilu="Testovací díl",
            zmena_mnozstvi=-2,
            mnozstvi=3,
            jednotky="ks",
            typ_operace="VÝDEJ",
            pouzite_zarizeni="HSH",
            umisteni="Sklad A",
            dodavatel="Test Dodavatel",
            datum_vydeje=date.today(),
            jednotkova_cena_eur=10.0,
            celkova_cena_eur=20.0,
            operaci_provedl=self.user,
            typ_udrzby="Preventivní",
            poznamka="Test výdej"
        )

        self.factory = RequestFactory()
        self.view = AuditLogListView()
        self.view.request = self.factory.get(reverse("audit_log"))
        self.view.request.user = self.user
        self.view.month = str(date.today().month)
        self.view.year = str(date.today().year)
        self.view.typ_udrzby = 'VŠE'
        self.view.ucetnictvi = ''
        self.view.query = ''

    def test_export_to_csv_contains_expected_data(self):
        """
        Ověřuje, že export do CSV vrací očekávaná data a formát.
        """
        queryset = AuditLog.objects.all()
        response = self.view.generate_export_to_csv(queryset)

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename="audit_log_export.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn("Testovací díl", content)
        self.assertIn("Test Dodavatel", content)
        self.assertIn("20.0", content)

    def test_export_consumption_to_csv_contains_expected_data(self):
        """
        Ověřuje, že export spotřeby do CSV vrací očekávaná data a formát.
        """
        queryset = AuditLog.objects.all()
        response = self.view.generate_export_consumption_to_csv(queryset)

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename="spotreba_export.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn("Testovací díl", content)
        self.assertIn("ks", content)
        self.assertIn("-2", content)

    def test_generate_graph_to_pdf_returns_file_response(self):
        """
        Ověřuje, že metoda generate_graph_to_pdf vrací FileResponse.
        """
        queryset = AuditLog.objects.all()
        response = self.view.generate_graph_to_pdf(queryset)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)

    def test_generate_graph_by_maintenance_returns_file_response(self):
        """
        Ověřuje, že metoda generate_graph_by_maintenance vrací FileResponse.
        """
        queryset = AuditLog.objects.all()
        response = self.view.generate_graph_by_maintenance(queryset)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)
