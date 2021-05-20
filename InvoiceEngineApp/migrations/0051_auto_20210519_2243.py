# Generated by Django 3.1.7 on 2021-05-19 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0050_remove_contracttype_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='date_next_prolongation',
            field=models.DateField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='vatrate',
            name='end_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]