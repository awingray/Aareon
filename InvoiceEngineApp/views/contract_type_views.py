from django.http import Http404
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import ContractTypeForm
from InvoiceEngineApp.models import ContractType
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
    ParentDetailView
)


class ContractTypeListView(ParentListView):
    template_name = 'InvoiceEngineApp/contract_type_list.html'
    model = ContractType


class ContractTypeCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractTypeForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract type"
        self.list_page = "contract_type_list"

    def form_valid(self, form):
        self.object = form.instance
        self.object.create(self.tenancy)
        return super().form_valid(form)


class ContractTypeUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractTypeForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract type"
        self.list_page = "contract_type_list"

    def get_object(self, queryset=ContractType.objects.all()):
        contract_type_id = self.kwargs.get('contract_type_id')
        qs = queryset.filter(contract_type_id=contract_type_id)
        qs = super().filter_by_tenancy(qs)
        contract_type = get_object_or_404(qs)

        if not contract_type.can_update_or_delete():
            raise Http404('No Contract type matches the given query.')
        return contract_type


class ContractTypeDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "contract type"
        self.list_page = "contract_type_list"

    def get_object(self, queryset=ContractType.objects.all()):
        contract_type_id = self.kwargs.get('contract_type_id')
        qs = queryset.filter(contract_type_id=contract_type_id)
        qs = super().filter_by_tenancy(qs)
        contract_type = get_object_or_404(qs)

        if not contract_type.can_update_or_delete():
            raise Http404('No Contract type matches the given query.')
        return contract_type
