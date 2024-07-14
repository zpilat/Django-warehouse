from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Poptavky, Dodavatele

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
