from django.http import Http404
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import (
    ContractForm,
    ContractSearchForm,
    ContractActivationForm,
    ContractDeactivationForm
)
from InvoiceEngineApp.models import Contract
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


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
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.tenancy)
        return form

    def form_valid(self, form):
        self.object = form.instance
        self.object.create(self.tenancy)
        return super().form_valid(form)


class ContractDetailView(ParentListView):
    """DetailView for contract.  It is implemented as a ListView because
    is has to list all invoices corresponding to the contract.
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
        contract = get_object_or_404(qs)

        if contract.can_update_or_delete():
            raise Http404('No Contract matches the given query.')

        return contract

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
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
        contract = get_object_or_404(qs)

        if contract.can_update_or_delete():
            raise Http404('No Contract matches the given query.')

        return contract


class ContractActivationView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractActivationForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(contract_id=contract_id)
        qs = super().filter_by_tenancy(qs)
        contract = get_object_or_404(qs)

        if contract.validate() != 100:
            raise Http404('No Contract matches the given query.')

        return contract


class ContractDeactivationView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractDeactivationForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract"
        self.list_page = "contract_list"

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        qs = queryset.filter(contract_id=contract_id)
        qs = super().filter_by_tenancy(qs)
        contract = get_object_or_404(qs)

        if not contract.start_date \
                or contract.can_update_or_delete() \
                or contract.end_date:
            raise Http404('No Contract matches the given query.')

        return contract
