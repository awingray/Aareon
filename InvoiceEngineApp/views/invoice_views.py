from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import csv
from InvoiceEngineApp.models import Invoice
from InvoiceEngineApp.views.parent_views import ParentListView, ParentDetailView


def invoice_export(request, company_id, queryset=Invoice.objects.all()):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="output.csv"'
    qs = queryset.filter(tenancy__tenancy_id=request.user.username)
    opts = qs.model._meta
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    writer.writerow(field_names)

    for obj in qs:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response


class InvoiceListView(ParentListView):
    template_name = "InvoiceEngineApp/invoice_list.html"
    model = Invoice


class InvoiceDetailView(ParentDetailView):
    template_name = "InvoiceEngineApp/details.html"

    def __init__(self):
        super().__init__()
        self.object_type = "invoice"
        self.list_page = "invoice_list"

    def get_object(self, queryset=Invoice.objects.all()):
        invoice_id = self.kwargs.get("invoice_id")
        qs = queryset.filter(invoice_id=invoice_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
