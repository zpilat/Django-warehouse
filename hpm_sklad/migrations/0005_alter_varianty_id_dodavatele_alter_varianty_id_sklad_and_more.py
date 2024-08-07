# Generated by Django 5.0.6 on 2024-07-03 12:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hpm_sklad', '0004_alter_varianty_cislo_varianty_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='varianty',
            name='id_dodavatele',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='varianty_dodavatele', to='hpm_sklad.dodavatele', verbose_name='Dodavatel'),
        ),
        migrations.AlterField(
            model_name='varianty',
            name='id_sklad',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='varianty_skladu', to='hpm_sklad.sklad', verbose_name='Skladová položka'),
        ),
        migrations.CreateModel(
            name='Poptavky',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum_vytvoreni', models.DateTimeField(auto_now_add=True, verbose_name='Datum vytvoření')),
                ('stav', models.CharField(choices=[('Tvorba', 'Ve tvorbě'), ('Poptáno', 'Poptáno'), ('Uzavřeno', 'Uzavřeno')], default='Tvorba', max_length=10, verbose_name='Stav poptávky')),
                ('dodavatel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poptavky', to='hpm_sklad.dodavatele', verbose_name='Dodavatel')),
            ],
            options={
                'verbose_name': 'Poptávka',
                'verbose_name_plural': 'Poptávky',
            },
        ),
        migrations.CreateModel(
            name='PoptavkaVarianty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mnozstvi', models.PositiveIntegerField()),
                ('jednotky', models.CharField(choices=[('ks', 'kus'), ('kg', 'kilogram'), ('par', 'pár'), ('l', 'litr'), ('m', 'metr'), ('baleni', 'balení')], max_length=10, verbose_name='Jednotky')),
                ('varianta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hpm_sklad.varianty')),
                ('poptavka', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hpm_sklad.poptavky')),
            ],
        ),
    ]
