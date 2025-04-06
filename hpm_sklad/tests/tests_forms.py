from django.test import TestCase
from django.urls import reverse

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_user_agents.utils import get_user_agent

from datetime import date

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
    def setUp(self):
        self.zarizeni = Zarizeni.objects.create(kod_zarizeni='HSH', nazev_zarizeni='HSH TQ7', umisteni='Hala 2', typ_zarizeni='Víceúčelová pec')

    def test_valid_form(self):
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': 'HSH',
                'zmena_mnozstvi': '2',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5
        )
        self.assertTrue(form.is_valid())

    def test_invalid_mnozstvi_above_max(self):
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': 'HSH',
                'zmena_mnozstvi': '10',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5
        )
        self.assertFalse(form.is_valid())
        self.assertIn('zmena_mnozstvi', form.errors)

    def test_missing_zarizeni(self):
        form = AuditLogDispatchForm(
            data={
                'datum_vydeje': date.today().isoformat(),
                'pouzite_zarizeni': '',
                'zmena_mnozstvi': '1',
                'typ_udrzby': 'Preventivní'
            },
            max_mnozstvi=5
        )
        self.assertFalse(form.is_valid())
        self.assertIn('pouzite_zarizeni', form.errors)