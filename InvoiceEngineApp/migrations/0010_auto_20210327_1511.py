# Generated by Django 3.1.7 on 2021-03-27 15:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0009_contractperson'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('invoice_id', models.AutoField(primary_key=True, serialize=False)),
                ('internal_customer_id', models.PositiveIntegerField()),
                ('external_customer_id', models.PositiveIntegerField()),
                ('description', models.CharField(max_length=50)),
                ('base_amount', models.FloatField()),
                ('vat_amount', models.FloatField(default=0.0)),
                ('total_amount', models.FloatField(default=0.0)),
                ('balance', models.FloatField(default=0.0)),
                ('date', models.DateField(auto_now_add=True)),
                ('expiration_date', models.DateField()),
                ('invoice_number', models.PositiveIntegerField()),
                ('general_ledger_account', models.CharField(max_length=10)),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.contract')),
            ],
        ),
        migrations.AddField(
            model_name='tenancy',
            name='days_until_invoice_expiration',
            field=models.PositiveSmallIntegerField(default=14),
        ),
        migrations.AlterField(
            model_name='contractperson',
            name='payment_method',
            field=models.CharField(choices=[('A', 'ai'), ('E', 'email'), ('S', 'sms'), ('L', 'letter'), ('I', 'invoice')], default='I', max_length=1),
        ),
        migrations.CreateModel(
            name='InvoiceLine',
            fields=[
                ('invoice_line_id', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=50)),
                ('vat_type', models.PositiveIntegerField()),
                ('base_amount', models.FloatField()),
                ('vat_amount', models.FloatField(default=0.0)),
                ('total_amount', models.FloatField(default=0.0)),
                ('invoice_number', models.FloatField()),
                ('general_ledger_account', models.CharField(max_length=10)),
                ('general_ledger_dimension_base_component', models.CharField(max_length=10)),
                ('general_ledger_dimension_contract_1', models.CharField(max_length=10)),
                ('general_ledger_dimension_contract_2', models.CharField(max_length=10)),
                ('general_ledger_dimension_vat', models.CharField(max_length=10)),
                ('unit_price', models.FloatField()),
                ('unit_id', models.CharField(max_length=10)),
                ('component', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.component')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='InvoiceEngineApp.invoice')),
            ],
        ),
    ]
