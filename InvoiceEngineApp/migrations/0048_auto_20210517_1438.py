# Generated by Django 3.1.7 on 2021-05-17 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0047_auto_20210517_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='start_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]