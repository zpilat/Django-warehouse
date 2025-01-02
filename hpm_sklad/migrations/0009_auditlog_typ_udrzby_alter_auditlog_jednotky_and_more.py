# Generated by Django 5.0.6 on 2025-01-02 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hpm_sklad', '0008_alter_historicalsklad_jednotky_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditlog',
            name='typ_udrzby',
            field=models.CharField(choices=[('Reaktivní', 'Reaktivní'), ('Preventivní', 'Preventivní'), ('Prediktivní', 'Prediktivní'), ('Ostatní', 'Ostatní')], max_length=20, null=True, verbose_name='Typ údržby'),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='jednotky',
            field=models.CharField(choices=[('ks', 'kus'), ('kg', 'kilogram'), ('pár', 'pár'), ('l', 'litr'), ('m', 'metr'), ('balení', 'balení')], default='ks', max_length=10, verbose_name='Jednotky'),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='typ_operace',
            field=models.CharField(choices=[('PŘÍJEM', 'Příjem'), ('VÝDEJ', 'Výdej')], max_length=10, null=True, verbose_name='Typ operace'),
        ),
    ]
