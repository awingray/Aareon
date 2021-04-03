from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import VATRateForm
from InvoiceEngineApp.models import VATRate
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
    ParentDetailView
)


class VATRateListView(ParentListView):
    template_name = 'InvoiceEngineApp/vat_rate_list.html'
    model = VATRate


class VATRateCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"


class VATRateDetailView(ParentDetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"

    def get_object(self, queryset=VATRate.objects.all()):
        vat_rate_id = self.kwargs.get('vat_rate_id')
        qs = queryset.filter(vat_rate_id=vat_rate_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class VATRateUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"

    def get_object(self, queryset=VATRate.objects.all()):
        vat_rate_id = self.kwargs.get('vat_rate_id')
        qs = queryset.filter(vat_rate_id=vat_rate_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class VATRateDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"

    def get_object(self, queryset=VATRate.objects.all()):
        vat_rate_id = self.kwargs.get('vat_rate_id')
        qs = queryset.filter(vat_rate_id=vat_rate_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
