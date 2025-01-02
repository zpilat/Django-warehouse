# Generated by Django 5.0.6 on 2025-01-02 10:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hpm_sklad', '0007_rename_id_dodavatele_varianty_dodavatel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalsklad',
            name='jednotky',
            field=models.CharField(choices=[('ks', 'kus'), ('kg', 'kilogram'), ('pár', 'pár'), ('l', 'litr'), ('m', 'metr'), ('balení', 'balení')], default='ks', max_length=10, verbose_name='Jednotky'),
        ),
        migrations.AlterField(
            model_name='poptavkavarianty',
            name='jednotky',
            field=models.CharField(choices=[('ks', 'kus'), ('kg', 'kilogram'), ('pár', 'pár'), ('l', 'litr'), ('m', 'metr'), ('balení', 'balení')], max_length=10, verbose_name='Jednotky'),
        ),
        migrations.AlterField(
            model_name='poptavkavarianty',
            name='mnozstvi',
            field=models.PositiveIntegerField(verbose_name='Množství'),
        ),
        migrations.AlterField(
            model_name='poptavkavarianty',
            name='poptavka',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poptavka', to='hpm_sklad.poptavky', verbose_name='Poptávka'),
        ),
        migrations.AlterField(
            model_name='poptavkavarianty',
            name='varianta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='varianta', to='hpm_sklad.varianty', verbose_name='Varianta'),
        ),
        migrations.AlterField(
            model_name='poptavky',
            name='dodavatel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poptavky_dodavatele', to='hpm_sklad.dodavatele', verbose_name='Dodavatel'),
        ),
        migrations.AlterField(
            model_name='sklad',
            name='jednotky',
            field=models.CharField(choices=[('ks', 'kus'), ('kg', 'kilogram'), ('pár', 'pár'), ('l', 'litr'), ('m', 'metr'), ('balení', 'balení')], default='ks', max_length=10, verbose_name='Jednotky'),
        ),
    ]
