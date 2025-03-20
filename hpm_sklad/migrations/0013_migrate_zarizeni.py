from django.db import migrations

def migrate_zarizeni(apps, schema_editor):
    Sklad = apps.get_model('hpm_sklad', 'Sklad')
    Zarizeni = apps.get_model('hpm_sklad', 'Zarizeni')

    # Mapa: název původního boolean sloupce -> id zařízení v tabulce Zarizeni
    field_to_zarizeni = {
        'hsh': 1,
        'tq8': 2,
        'tqf_xl1': 3,
        'tqf_xl2': 4,
        'dc_xl': 5,
        'dac_xl1_2': 6,
        'dl_xl': 7,
        'dac': 8,
        'lac_1': 9,
        'lac_2': 10,
        'ipsen_ene': 11,
        'hsh_ene': 12,
        'xl_ene1': 13,
        'xl_ene2': 14,
        'ipsen_w': 15,
        'hsh_w': 16,
        'kw': 17,
        'kw1': 18,
        'kw2': 19,
        'kw3': 20,
        'mikrof': 21,
    }


    for sklad in Sklad.objects.all():
        for field, zarizeni_id in field_to_zarizeni.items():
            if getattr(sklad, field):  # pokud je hodnota sloupce True
                try:
                    device = Zarizeni.objects.get(id=zarizeni_id)
                    sklad.zarizeni.add(device)
                except Zarizeni.DoesNotExist as e:
                    # Pokud by záznam zařízení neexistoval
                    print(f'Takové zařízení neexistuje: {e}')


class Migration(migrations.Migration):

    dependencies = [
        ('hpm_sklad', '0012_sklad_zarizeni'),
    ]

    operations = [
        migrations.RunPython(migrate_zarizeni),
    ]
