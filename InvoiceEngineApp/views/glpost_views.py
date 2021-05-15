from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import csv

# from InvoiceEngineApp.forms import
from InvoiceEngineApp.models import GeneralLedgerPost
from InvoiceEngineApp.views.parent_views import ParentListView, ParentDetailView


def glpost_export(request, company_id, queryset=GeneralLedgerPost.objects.all()):
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


class GLPostListView(ParentListView):
    template_name = "InvoiceEngineApp/glpost_list.html"
    model = GeneralLedgerPost


class GLPostDetailView(ParentDetailView):
    template_name = "InvoiceEngineApp/details.html"

    def __init__(self):
        super().__init__()
        self.object_type = "general ledger post"
        self.list_page = "glpost_list"

    def get_object(self, queryset=GeneralLedgerPost.objects.all()):
        generalledgerpost_id = self.kwargs.get("id")
        qs = queryset.filter(general_ledger_post_id=generalledgerpost_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
