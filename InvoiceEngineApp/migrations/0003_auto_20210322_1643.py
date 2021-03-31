# Generated by Django 3.1.7 on 2021-03-22 16:43

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0002_auto_20210322_1229'),
    ]

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('component_id', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=50)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('end_date_prolong', models.DateField()),
                ('next_date_prolong', models.DateField()),
                ('invoice_number', models.FloatField()),
                ('base_amount', models.FloatField()),
                ('vat_amount', models.FloatField()),
                ('total_amount', models.FloatField()),
                ('unit_id', models.CharField(max_length=10)),
                ('unit_amount', models.FloatField()),
            ],
        ),
        migrations.RemoveConstraint(
            model_name='contract',
            name='check_period',
        ),
        migrations.AddConstraint(
            model_name='contract',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('invoicing_amount_of_days', True), ('invoicing_period', 'V'), ('invoicing_start_day', None)), models.Q(('invoicing_amount_of_days', None), ('invoicing_period', False), ('invoicing_start_day', True)), _connector='OR'), name='check_period'),
        ),
        migrations.AddConstraint(
            model_name='contract',
            constraint=models.CheckConstraint(check=models.Q(end_date__gt=django.db.models.expressions.F('start_date')), name='contract_start_before_end'),
        ),
        migrations.AddField(
            model_name='component',
            name='base_component',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.basecomponent'),
        ),
        migrations.AddField(
            model_name='component',
            name='contract',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.contract'),
        ),
        migrations.AddField(
            model_name='component',
            name='vat_rate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.vatrate'),
        ),
        migrations.AddConstraint(
            model_name='component',
            constraint=models.CheckConstraint(check=models.Q(end_date__gt=django.db.models.expressions.F('start_date')), name='component_start_before_end'),
        ),
    ]
