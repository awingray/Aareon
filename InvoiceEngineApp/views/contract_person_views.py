from django.http import Http404
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

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables, set the tenancy and the contract, and then check if
        it's valid.
        """
        self.object = None

        form = self.get_form()
        form.instance.create(self.tenancy, self.kwargs.get('contract_id'))
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.instance
        self.object.create(self.tenancy, self.kwargs.get('contract_id'))
        return super().form_valid(form)


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
        contract_person = get_object_or_404(qs)

        if not contract_person.can_update_or_delete():
            raise Http404('No Contract person matches the given query.')

        return contract_person


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
        contract_person = get_object_or_404(qs)

        if not contract_person.can_update_or_delete():
            raise Http404('No Contract person matches the given query.')

        return contract_person
