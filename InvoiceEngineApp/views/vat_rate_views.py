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
from InvoiceEngineApp.models import VATRate, Tenancy
from InvoiceEngineApp.forms import VATRateForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class VATRateListView(ListView):
    template_name = 'InvoiceEngineApp/vat_rate_list.html'

    def get_queryset(self):
        id_ = self.kwargs.get('company_id')
        return VATRate.objects.filter(tenancy=get_object_or_404(Tenancy, company_id=id_))

    # Maybe this guy is not necessary?
    def get(self, request, *args, **kwargs):
        context = {'object_list': self.get_queryset(), 'company_id': self.kwargs.get('company_id')}
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class VATRateCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = VATRateForm

    def get_context_data(self, **kwargs):
        context = super(VATRateCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "VAT rate"
        context['list_page'] = ["vat_rate_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # Add the reference to the proper tenancy to the vat rate.
        company_id = self.kwargs.get('company_id')
        form.set_tenancy(company_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vat_rate_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class VATRateDetailView(DetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def get_context_data(self, **kwargs):
        context = super(VATRateDetailView, self).get_context_data(**kwargs)
        context['object_type'] = "VAT rate"
        context['list_page'] = ["vat_rate_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=VATRate.objects.all()):
        id_ = self.kwargs.get('vat_rate_id')
        return get_object_or_404(VATRate, vat_rate_id=id_)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class VATRateUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = VATRateForm
    extra_context = {'object_type': "VAT rate"}

    def get_object(self, queryset=VATRate.objects.all()):
        id_ = self.kwargs.get('vat_rate_id')
        return get_object_or_404(VATRate, vat_rate_id=id_)

    def get_success_url(self):
        return reverse('vat_rate_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class VATRateDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(VATRateDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "VAT rate"
        context['list_page'] = ["vat_rate_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=VATRate.objects.all()):
        id_ = self.kwargs.get('vat_rate_id')
        return get_object_or_404(VATRate, vat_rate_id=id_)

    def get_success_url(self):
        return reverse('vat_rate_list', args=[self.kwargs.get('company_id')])
