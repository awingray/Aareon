from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView
)
from InvoiceEngineApp.models import ContractPerson
from InvoiceEngineApp.forms import ContractPersonForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractPersonCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractPersonForm

    def get_context_data(self, **kwargs):
        context = super(ContractPersonCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "contract person"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # Add the reference to the proper contract.
        contract_id = self.kwargs.get('contract_id')
        form.finalize_creation(contract_id)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractPersonUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractPersonForm
    extra_context = {'object_type': "contract person"}

    def get_object(self, queryset=ContractPerson.objects.all()):
        contract_person_id = self.kwargs.get('contract_person_id')
        return get_object_or_404(ContractPerson, contract_person_id=contract_person_id)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractPersonDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(ContractPersonDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "contract person"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=ContractPerson.objects.all()):
        contract_person_id = self.kwargs.get('contract_person_id')
        return get_object_or_404(ContractPerson, contract_person_id=contract_person_id)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])
