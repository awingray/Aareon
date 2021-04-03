from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import ContractForm
from InvoiceEngineApp.models import Contract
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
    ParentDetailView
)


class ContractListView(ParentListView):
    template_name = 'InvoiceEngineApp/contract_list.html'
    model = Contract


class ContractCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the tenancy."""
        form = super().get_form()
        form.filter_selectors(self.tenancy)
        return form


class ContractDetailView(ParentDetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(contract_id=contract_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class ContractUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(contract_id=contract_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the tenancy."""
        form = super().get_form()
        form.filter_selectors(self.object.tenancy)
        return form


class ContractDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(contract_id=contract_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)

    def delete(self, request, *args, **kwargs):
        contract = self.get_object()

        # Update the tenancy: there is one fewer contract now
        contract.tenancy.number_of_contracts -= 1
        contract.tenancy.clean()
        contract.tenancy.save()

        contract.delete()
        return HttpResponseRedirect(self.get_success_url())
