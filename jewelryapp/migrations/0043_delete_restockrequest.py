# Generated by Django 5.1 on 2025-01-29 09:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0042_remove_supplierproduct_supplier_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RestockRequest',
        ),
    ]
