from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import ContractForm, ContractSearchForm
from InvoiceEngineApp.models import Contract, Invoice
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)

import csv


def export(request):
    #res = HttpResponse(content_type='text/csv')

    #writer = csv.writer(res)
    # writer.writerow()

    #res['Content-Disposition'] = 'attachment; filename="out.csv"'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="file.csv"'
    obj = Contract.objects.all()
    writer = csv.writer(response)
    for contract in obj:
        writer.writerow([contract.contract_id, contract.contract_type])
    return response


class ContractListView(ParentListView):
    template_name = 'InvoiceEngineApp/contract_list.html'
    form_class = ContractSearchForm
    model = Contract

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(self.request.GET)
        return context

    def get_queryset(self):
        # Get the contract list filtered by tenancy
        qs = super().get_queryset()
        form = self.form_class(self.request.GET)

        # Filter the contract list further by user input
        if form.is_valid():
            return form.filter_queryset(qs)
        return qs


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


class ContractDetailView(ParentListView):
    """DetailView for contract.  It is implemented as a ListView because is has to list all invoices
    corresponding to the contract.
    """
    template_name = 'InvoiceEngineApp/contract_details.html'

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"
        self.object = None

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(
            contract_id=contract_id,
            tenancy__tenancy_id=self.request.user.username
        )
        return get_object_or_404(qs)

    def get_queryset(self):
        self.object = self.get_object()
        return self.object.get_invoices()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.object
        context['list_page'] = [
            self.list_page,
            self.kwargs.get('company_id')
        ]
        return context


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
