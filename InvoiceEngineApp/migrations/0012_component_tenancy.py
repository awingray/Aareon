# Generated by Django 3.1.7 on 2021-04-03 09:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0011_invoice_tenancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='tenancy',
            field=models.ForeignKey(default=27, on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.tenancy'),
            preserve_default=False,
        ),
    ]
