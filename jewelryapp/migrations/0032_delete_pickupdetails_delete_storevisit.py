# Generated by Django 5.1 on 2025-01-26 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0031_storevisit'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PickupDetails',
        ),
        migrations.DeleteModel(
            name='StoreVisit',
        ),
    ]
