from django.http import Http404
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import VATRateForm
from InvoiceEngineApp.models import VATRate
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


class VATRateListView(ParentListView):
    template_name = 'InvoiceEngineApp/vat_rate_list.html'
    model = VATRate

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('type', 'start_date')


class VATRateCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"

    def form_valid(self, form):
        self.object = form.instance
        self.object.create(self.tenancy)
        return super().form_valid(form)


class VATRateUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.list_page = "vat_rate_list"

    def get_object(self, queryset=VATRate.objects.all()):
        vat_rate_id = self.kwargs.get('vat_rate_id')
        qs = queryset.filter(
            vat_rate_id=vat_rate_id
        )
        qs = super().filter_by_tenancy(qs)
        vat_rate = get_object_or_404(qs)
        if not vat_rate.can_update_or_delete():
            # Maybe make a page for this that informs the user of which
            # components prevent this VAT rate from being deactivated
            raise Http404('No VAT rate matches the given query.')
        return vat_rate

    def form_valid(self, form):
        self.object = form.instance
        self.object.update_components()
        return super().form_valid(form)


class VATRateDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "VAT rate"
        self.list_page = "vat_rate_list"

    def get_object(self, queryset=VATRate.objects.all()):
        vat_rate_id = self.kwargs.get('vat_rate_id')
        qs = queryset.filter(
            vat_rate_id=vat_rate_id
        )
        qs = super().filter_by_tenancy(qs)
        vat_rate = get_object_or_404(qs)
        if not vat_rate.can_update_or_delete():
            # Maybe make a page for this that informs the user of which
            # components prevent this VAT rate from being deactivated
            raise Http404('No VAT rate matches the given query.')
        return vat_rate

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
