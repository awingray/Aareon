# Generated by Django 3.1.7 on 2021-06-13 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0053_auto_20210521_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='pricing_type',
            field=models.CharField(choices=[('P', 'Per period'), ('D', 'Per day')], default='P', max_length=1),
        ),
    ]