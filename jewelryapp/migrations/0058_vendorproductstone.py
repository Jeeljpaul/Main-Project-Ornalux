# Generated by Django 5.1 on 2025-02-27 04:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0057_remove_vendorproduct_price_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorProductStone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_diamond', models.BooleanField(default=False)),
                ('diamond_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('diamond_count', models.IntegerField(blank=True, null=True)),
                ('diamond_quality', models.CharField(blank=True, max_length=50, null=True)),
                ('stone_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('stone_count', models.IntegerField(blank=True, null=True)),
                ('stone_clarity', models.CharField(blank=True, max_length=50, null=True)),
                ('stone_cost', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('stone_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jewelryapp.stonetype')),
                ('vendor_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stones', to='jewelryapp.vendorproduct')),
            ],
        ),
    ]
