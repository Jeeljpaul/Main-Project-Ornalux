# Generated by Django 5.1 on 2024-10-10 05:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0005_productattribute'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
        migrations.RemoveField(
            model_name='product',
            name='metal_type',
        ),
        migrations.RemoveField(
            model_name='product',
            name='stone_type',
        ),
    ]
