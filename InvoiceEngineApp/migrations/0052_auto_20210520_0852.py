# Generated by Django 3.1.7 on 2021-05-20 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0051_auto_20210519_2243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='start_date',
            field=models.DateField(null=True),
        ),
    ]
