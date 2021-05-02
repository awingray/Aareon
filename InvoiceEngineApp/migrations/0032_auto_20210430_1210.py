# Generated by Django 3.1.7 on 2021-04-30 12:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0031_auto_20210429_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='component',
            name='vat_rate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.vatrate'),
        ),
    ]