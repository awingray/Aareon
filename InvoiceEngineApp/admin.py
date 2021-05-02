from django.contrib import admin
from InvoiceEngineApp.models import (
    Tenancy,
    VATRate,
    ContractType,
    BaseComponent,
    Contract,
    Component,
    Invoice,
    InvoiceLine,
    Collection,
    GeneralLedgerPost
)

admin.site.register(Tenancy)
admin.site.register(VATRate)
admin.site.register(ContractType)
admin.site.register(BaseComponent)
admin.site.register(Contract)
admin.site.register(Component)
admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(Collection)
admin.site.register(GeneralLedgerPost)
