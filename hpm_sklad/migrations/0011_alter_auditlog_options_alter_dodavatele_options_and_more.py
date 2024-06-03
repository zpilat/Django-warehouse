# Generated by Django 5.0.6 on 2024-05-31 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hpm_sklad", "0010_alter_sklad_options_alter_auditlog_nazev_dilu_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="auditlog",
            options={"verbose_name_plural": "Auditovací logy"},
        ),
        migrations.AlterModelOptions(
            name="dodavatele",
            options={"verbose_name_plural": "Dodavatelé"},
        ),
        migrations.AlterModelOptions(
            name="historicalsklad",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical sklad",
                "verbose_name_plural": "historical Sklady",
            },
        ),
        migrations.AlterModelOptions(
            name="sklad",
            options={"ordering": ["-evidencni_cislo"], "verbose_name_plural": "Sklady"},
        ),
        migrations.AlterModelOptions(
            name="zarizeni",
            options={"verbose_name_plural": "Zařízení"},
        ),
        migrations.AlterField(
            model_name="auditlog",
            name="pouzite_zarizeni",
            field=models.CharField(max_length=70, verbose_name="Pro zařízení"),
        ),
        migrations.AlterField(
            model_name="historicalsklad",
            name="dodavatel",
            field=models.CharField(
                blank=True, max_length=70, null=True, verbose_name="Dodavatel"
            ),
        ),
        migrations.AlterField(
            model_name="sklad",
            name="dodavatel",
            field=models.CharField(
                blank=True, max_length=70, null=True, verbose_name="Dodavatel"
            ),
        ),
    ]