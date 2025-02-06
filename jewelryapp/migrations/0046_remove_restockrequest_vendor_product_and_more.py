# Generated by Django 5.1 on 2025-02-01 05:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0045_product_vendor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='restockrequest',
            name='vendor_product',
        ),
        migrations.RemoveField(
            model_name='vendorproduct',
            name='category',
        ),
        migrations.RemoveField(
            model_name='vendorproduct',
            name='metaltype',
        ),
        migrations.RemoveField(
            model_name='vendorproduct',
            name='vendor',
        ),
        migrations.DeleteModel(
            name='NewProductRequest',
        ),
        migrations.DeleteModel(
            name='RestockRequest',
        ),
        migrations.DeleteModel(
            name='VendorProduct',
        ),
    ]
