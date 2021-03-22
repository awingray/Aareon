# Generated by Django 3.1.7 on 2021-03-22 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0004_auto_20210322_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='balance',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='contract',
            name='base_amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='contract',
            name='total_amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='contract',
            name='vat_amount',
            field=models.FloatField(default=0.0),
        ),
    ]
