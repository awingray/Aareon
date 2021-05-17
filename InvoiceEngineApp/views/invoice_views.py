from django.shortcuts import get_object_or_404

from InvoiceEngineApp.models import Invoice
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentDetailView
)


class InvoiceListView(ParentListView):
    template_name = 'InvoiceEngineApp/invoice_list.html'
    model = Invoice

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('invoice_number')


class InvoiceDetailView(ParentDetailView):
    template_name = 'InvoiceEngineApp/invoice_details.html'

    def __init__(self):
        super().__init__()
        self.object_type = "invoice"
        self.list_page = "invoice_list"

    def get_object(self, queryset=Invoice.objects.all()):
        invoice_id = self.kwargs.get('invoice_id')
        qs = queryset.filter(invoice_id=invoice_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
