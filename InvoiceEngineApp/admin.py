from django.contrib import admin

from InvoiceEngineApp.models import Tenancy, VATRate, ContractType

admin.site.register(Tenancy)
admin.site.register(VATRate)
admin.site.register(ContractType)
