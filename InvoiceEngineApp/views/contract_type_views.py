from django.contrib.auth.decorators import login_required
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
from InvoiceEngineApp.models import ContractType, Tenancy
from InvoiceEngineApp.forms import ContractTypeForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractTypeListView(ListView):
    template_name = 'InvoiceEngineApp/contract_type_list.html'

    def get_queryset(self):
        id_ = self.kwargs.get('company_id')
        return ContractType.objects.filter(tenancy=get_object_or_404(Tenancy, company_id=id_))

    # Maybe this guy is not necessary?
    def get(self, request, *args, **kwargs):
        context = {'object_list': self.get_queryset(), 'company_id': self.kwargs.get('company_id')}
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractTypeCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ContractTypeForm

    def get_context_data(self, **kwargs):
        context = super(ContractTypeCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "contract type"
        context['list_page'] = ["contract_type_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # This may be too much logic in the view, not sure.
        # Add the reference to the proper tenancy to the contract type.
        id_ = self.kwargs.get('company_id')
        form.instance.tenancy = get_object_or_404(Tenancy, company_id=id_)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contract_type_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractTypeDetailView(DetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def get_context_data(self, **kwargs):
        context = super(ContractTypeDetailView, self).get_context_data(**kwargs)
        context['object_type'] = "contract type"
        context['list_page'] = ["contract_type_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=ContractType.objects.all()):
        id_ = self.kwargs.get('contract_type_id')
        return get_object_or_404(ContractType, contract_type_id=id_)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractTypeUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ContractTypeForm
    extra_context = {'object_type': "contract type"}

    def get_object(self, queryset=ContractType.objects.all()):
        id_ = self.kwargs.get('contract_type_id')
        return get_object_or_404(ContractType, contract_type_id=id_)

    def get_success_url(self):
        return reverse('contract_type_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ContractTypeDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(ContractTypeDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "contract type"
        context['list_page'] = ["contract_type_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=ContractType.objects.all()):
        id_ = self.kwargs.get('contract_type_id')
        return get_object_or_404(ContractType, contract_type_id=id_)

    def get_success_url(self):
        return reverse('contract_type_list', args=[self.kwargs.get('company_id')])
