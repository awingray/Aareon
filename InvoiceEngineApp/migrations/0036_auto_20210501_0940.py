# Generated by Django 3.1.7 on 2021-05-01 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0035_auto_20210430_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='invoiceline',
            name='general_ledger_dimension_vat',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceline',
            name='vat_type',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='tenancy',
            name='last_invoice_number',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
