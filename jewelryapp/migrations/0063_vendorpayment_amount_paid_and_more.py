# Generated by Django 5.1 on 2025-03-04 02:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jewelryapp', '0062_stonepurity'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorpayment',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='vendorpayment',
            name='payment_purpose',
            field=models.CharField(choices=[('purchase', 'Product Purchase'), ('restock', 'Restock Request')], default='purchase', max_length=20),
        ),
        migrations.AddField(
            model_name='vendorpayment',
            name='remaining_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='payment_type',
            field=models.CharField(choices=[('advance', 'Advance Payment'), ('half', 'Half Payment'), ('post', 'Post Delivery Payment')], default='post', max_length=50),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('partial_paid', 'Partially Paid'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('notification_type', models.CharField(max_length=50)),
                ('related_id', models.IntegerField(null=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jewelryapp.tbl_login')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='VendorPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255)),
                ('quantity', models.PositiveIntegerField()),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('expected_arrival', models.DateField()),
                ('requested_arrival_date', models.DateField(blank=True, null=True)),
                ('has_date_update_request', models.BooleanField(default=False)),
                ('purchase_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('is_user_purchased', models.BooleanField(default=False)),
                ('user_purchased_count', models.PositiveIntegerField(default=0)),
                ('payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='jewelryapp.vendorpayment')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jewelryapp.vendor')),
            ],
        ),
    ]
