# Generated by Django 5.1 on 2025-02-25 05:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0056_review_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendorproduct',
            name='price',
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='bis_hallmark',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='diamond_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='diamond_quality',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='diamond_weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='estimated_delivery',
            field=models.IntegerField(default=7),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='home_delivery',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='image2',
            field=models.ImageField(blank=True, null=True, upload_to='vendor_products/'),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='image3',
            field=models.ImageField(blank=True, null=True, upload_to='vendor_products/'),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='image4',
            field=models.ImageField(blank=True, null=True, upload_to='vendor_products/'),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='making_charges',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='metal_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='product_video',
            field=models.FileField(blank=True, null=True, upload_to='vendor_products/videos/'),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='purity',
            field=models.IntegerField(default=22),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='stone_clarity',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='stone_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='stone_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='stone_weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='store_pickup',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='vendorproduct',
            name='try_at_home',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='vendorproduct',
            name='gender',
            field=models.CharField(choices=[('Men', 'Men'), ('Women', 'Women'), ('Unisex', 'Unisex'), ('Kids', 'Kids'), ('Baby', 'Baby')], default='Unisex', max_length=50),
        ),
        migrations.AlterField(
            model_name='vendorproduct',
            name='stock_quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='vendorproduct',
            name='stonetype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jewelryapp.stonetype'),
        ),
        migrations.AlterField(
            model_name='vendorproduct',
            name='weight',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
    ]
