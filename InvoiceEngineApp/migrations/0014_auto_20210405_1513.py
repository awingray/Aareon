# Generated by Django 3.1.7 on 2021-04-05 15:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0013_contractperson_tenancy'),
    ]

    operations = [
        migrations.RenameField(
            model_name='component',
            old_name='invoice_number',
            new_name='number_of_units',
        ),
    ]