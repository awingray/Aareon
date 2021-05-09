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

"""     example export function

Name: Name from cpers
Adress: Address from cpers
City: City from cpers
Payment method: Pay_meth from cpers
Payment day: Pay_day from cpers
Invoice number: Inv_nr  from inv
Invoice date: Inv_date from inv
**Contract ID: Contr_id from cpers
Invoice ID: Inv_id from inv
***Invoice amount: Inv_amt from invinc
Mandate: Mandaat form cpers
IBAN: Iban form cpers
Email: Email form cpers
Phone: Phone from cpers*



** is it contract id or contract person id?

*** invoice amount == total_amount?

 """


def export(request, company_id, contract_id, queryset=Contract.objects.all()):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="output.csv"'
    qs = queryset.filter(
        contract_id=contract_id,
        tenancy__tenancy_id=request.user.username
    )
    cpers = qs.get().get_contract_persons().get()
    invs = qs.get().get_invoices().get()
    writer = csv.writer(response)
    # Use exclude to omit the fields instead of manually define the field names - Awin
    fields = ['name', 'address', 'city', 'payment_method', 'payment_day',
              'invoice_number', 'date', 'contract_person_id', 'invoice_id', 'total_amount',
              'mandate', 'iban', 'email']
    writer.writerow(fields)
    val = [cpers.name, cpers.address, cpers.city, cpers.payment_method, cpers.payment_day,
           invs.invoice_number, invs.date, cpers.contract_person_id, invs.invoice_id, invs.total_amount,
           cpers.mandate, cpers.iban, cpers.email]
    print(val)
    for obj in qs:
        writer.writerow(val)

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
