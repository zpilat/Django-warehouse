from django.test import TestCase
from django.urls import reverse

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_user_agents.utils import get_user_agent

from datetime import date, timedelta

from hpm_sklad.models import Poptavky, Dodavatele, Sklad, Zarizeni, SkladZarizeni, AuditLog, Varianty, PoptavkaVarianty
from hpm_sklad.forms import SkladReceiptForm, AuditLogReceiptForm, SkladDispatchForm, AuditLogDispatchForm


######################## Testy Formulářů ###########################

class SkladDispatchFormTest(TestCase):
    """
    Testy pro formulář `SkladDispatchForm`, který slouží k zaznamenání umístění a poznámky při výdeji.

    Testuje:
    - validaci správného vstupu
    - volitelnost poznámky a umístění
    """
    
    def test_valid_form(self):
        """Ověřuje, že formulář je validní při zadání všech správných hodnot."""
        form = SkladDispatchForm(data={
            'umisteni': 'Regál A3',
            'poznamka': 'Vydáno na opravu'
        })
        self.assertTrue(form.is_valid())

    def test_empty_poznamka_ok(self):
        """Ověřuje, že prázdné umístění nebo žádná poznámka nevadí (jsou volitelné)."""
        form = SkladDispatchForm(data={
            'umisteni': '',
            'poznamka': ''
        })
        self.assertTrue(form.is_valid())


class AuditLogDispatchFormTest(TestCase):
    """
    Testovací třída pro formulář `AuditLogDispatchForm`.

    Testuje následující scénáře:
    - Validita formuláře při správně zadaných datech.
    - Nevalidita formuláře při překročení maximálního množství.
    - Nevalidita formuláře při chybějícím výběru zařízení.
    - Nevalidita formuláře při nesprávném datu výdeje - zítřejší datum.
    """

    def setUp(self):
        """
        Vytvoří testovací zařízení, dodavatele, skladovou položku a vztah mezi nimi pro použití ve formuláři.
        """
        self.dodavatel = Dodavatele.objects.create(
            dodavatel="Test dodavatel"
        )

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
        

    def test_valid_form(self):
        """
        Ověřuje, že formulář je validní, pokud jsou všechna data správně zadána
        a množství nepřesahuje povolené maximum.
        """
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': 'HSH',
                'zmena_mnozstvi': '2',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5,
            zarizeni=self.sklad.zarizeni.all()
        )
        self.assertTrue(form.is_valid())

    def test_invalid_mnozstvi_above_max(self):
        """
        Ověřuje, že formulář je nevalidní, pokud je zadané množství vyšší než maximální povolené.
        """
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': 'HSH',
                'zmena_mnozstvi': '10',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5,
            zarizeni=self.sklad.zarizeni.all()            
        )
        self.assertFalse(form.is_valid())
        self.assertIn('zmena_mnozstvi', form.errors)

    def test_missing_zarizeni(self):
        """
        Ověřuje, že formulář je nevalidní, pokud není vybráno žádné zařízení.
        """
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': '',
                'zmena_mnozstvi': '1',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5,
            zarizeni=self.sklad.zarizeni.all()            
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pouzite_zarizeni', form.errors)

    def test_invalid_date(self):
        """
        Ověřuje, že formulář není validní, pokud je datum větší než aktuální.
        """
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': (date.today() + timedelta(days=1)).isoformat(),
                'pouzite_zarizeni': 'HSH',
                'zmena_mnozstvi': '2',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5,
            zarizeni=self.sklad.zarizeni.all()            
        )
        self.assertFalse(form.is_valid())  


class SkladReceiptFormTest(TestCase):
    """
    Testovací třída pro formulář `SkladReceiptForm`.

    Testuje následující scénáře:
    - Validita formuláře při správně zadaných datech.
    - Nevalidita formuláře při chybějících povinných polích.
    - Validita formuláře při chybějících nepovinných polích.
    - Nevalidita formuláře při zítřejším datu příjmu
    """
    def setUp(self):
        """
        Vytvoří testovacího dodavatele pro použití ve formuláři
        """
        self.dodavatel = Dodavatele.objects.create(
            dodavatel="Testovací dodavatel",
            kontakt="Kontaktní osoba",
            email="zkouska@email.cz",
            telefon="0124587952",
            jazyk="CZ"
        )

    def test_valid_form(self):
        """
        Ověřuje, že formulář je validní při zadání všech povinných dat.
        """
        form = SkladReceiptForm(data=
            {
                "objednano": "další není",
                "umisteni": "garáž L6",
                "dodavatel": self.dodavatel,
                "datum_nakupu": date.today().isoformat(),
                "cislo_objednavky": "237",
                "jednotkova_cena_eur": "2.5",
                "poznamka": "vyzkoušet",
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        """
        Ověřuje, že formulář je nevalidní, pokud není zadáno číslo objednávky.
        """
        form = SkladReceiptForm(data=
            {
                "objednano": "další není",
                "umisteni": "garáž L6",
                "dodavatel": self.dodavatel,
                "datum_nakupu": date.today().isoformat(),
                "cislo_objednavky": "",
                "jednotkova_cena_eur": "2.5",
                "poznamka": "vyzkoušet",
            }
        )
        self.assertFalse(form.is_valid())        

    def test_empty_poznamka_ok(self):
        """
        Ověřuje, že prázdné pole objednano nebo žádná poznámka nevadí (jsou volitelné).
        """
        form = SkladReceiptForm(data=
            {
                "objednano": "",
                "umisteni": "garáž L6",
                "dodavatel": self.dodavatel,
                "datum_nakupu": date.today().isoformat(),
                "cislo_objednavky": "237",
                "jednotkova_cena_eur": "2.5",
                "poznamka": "",
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_date(self):
        """
        Ověřuje, že formulář není validní při zadání zítřejšího data.
        """
        form = SkladReceiptForm(data=
            {
                "objednano": "další není",
                "umisteni": "garáž L6",
                "dodavatel": self.dodavatel,
                "datum_nakupu": (date.today() + timedelta(days=1)).isoformat(),
                "cislo_objednavky": "237",
                "jednotkova_cena_eur": "2.5",
                "poznamka": "vyzkoušet",
            }
        )
        self.assertFalse(form.is_valid())        


class AuditLogReceiptFormTest(TestCase):
    """
    Testovací třída pro formulář `AuditLogReceiptForm`

    Testuje následující scénáře:
    - Validita formuláře při správně zadaných datech.
    - Nevalidita formuláře při chybějící změně množství.
    """

    def test_valid_form(self):
        """
        Ověřuje, že formulář je validní, pokud jsou všechna data správně zadána.
        """
        form = AuditLogReceiptForm(
            data={
                'zmena_mnozstvi': '2',
            },
        )
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        """
        Ověřuje, že formulář je nevalidní, pokud je zadané množství rovné nule.
        """
        form = AuditLogReceiptForm(
            data={
                'zmena_mnozstvi': '0',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('zmena_mnozstvi', form.errors)
        