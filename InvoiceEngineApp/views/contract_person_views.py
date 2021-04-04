from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import ContractPersonForm
from InvoiceEngineApp.models import ContractPerson
from InvoiceEngineApp.views.parent_views import (
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView
)


class ContractPersonCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractPersonForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract person"
        self.list_page = "contract_list"


class ContractPersonUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractPersonForm

    def __init__(self):
        super().__init__()
        self.object_type = "contract person"
        self.list_page = "contract_list"

    def get_object(self, queryset=ContractPerson.objects.all()):
        contract_person_id = self.kwargs.get('contract_person_id')
        qs = queryset.filter(contract_person_id=contract_person_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class ContractPersonDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "contract person"
        self.list_page = "contract_list"

    def get_object(self, queryset=ContractPerson.objects.all()):
        contract_person_id = self.kwargs.get('contract_person_id')
        qs = queryset.filter(contract_person_id=contract_person_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
