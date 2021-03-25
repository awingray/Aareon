from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView
)
from InvoiceEngineApp.models import Contract, Tenancy
from InvoiceEngineApp.forms import ContractForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractListView(ListView):
    template_name = 'InvoiceEngineApp/contract_list.html'

    def get_queryset(self):
        id_ = self.kwargs.get('company_id')
        return Contract.objects.filter(tenancy=get_object_or_404(Tenancy, company_id=id_))

    def get(self, request, *args, **kwargs):
        context = {'contract_list': self.get_queryset(),
                   'company_id': self.kwargs.get('company_id')
                   }
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractForm

    def get_form_kwargs(self):
        """Overloaded to add the company id to the kwargs so the selection can be filtered."""
        kwargs = super(ContractCreateView, self).get_form_kwargs()
        kwargs['company_id'] = self.kwargs.get('company_id')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ContractCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "contract"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # Add the reference to the proper tenancy to the contract.
        company_id = self.kwargs.get('company_id')
        form.set_tenancy(company_id)

        return super().form_valid(form)

        # Do error handling!
        # try:
        #     return super().form_valid(form)
        # except IntegrityError as ie:
        #     return redirect(reverse('contract_create', args=[self.kwargs.get('company_id')]))

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractDetailView(DetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def get_context_data(self, **kwargs):
        context = super(ContractDetailView, self).get_context_data(**kwargs)
        context['object_type'] = "contract"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=Contract.objects.all()):
        id_ = self.kwargs.get('contract_id')
        return get_object_or_404(Contract, contract_id=id_)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractForm
    extra_context = {'object_type': "contract"}

    def get_form_kwargs(self):
        """Overloaded to add the company id to the kwargs so the selection for Tenancy can be filtered."""
        kwargs = super(ContractUpdateView, self).get_form_kwargs()
        kwargs['company_id'] = self.kwargs.get('company_id')
        return kwargs

    def get_object(self, queryset=Contract.objects.all()):
        id_ = self.kwargs.get('contract_id')
        return get_object_or_404(Contract, contract_id=id_)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(ContractDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "contract"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=Contract.objects.all()):
        contract_id = self.kwargs.get('contract_id')
        return get_object_or_404(Contract, contract_id=contract_id)

    def delete(self, request, *args, **kwargs):
        contract = self.get_object()

        contract.tenancy.number_of_contracts -= 1
        contract.tenancy.clean()
        contract.tenancy.save()

        contract.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])
