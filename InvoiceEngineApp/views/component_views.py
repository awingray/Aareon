from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView
)
from InvoiceEngineApp.models import Component
from InvoiceEngineApp.forms import ComponentForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ComponentCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ComponentForm

    def get_form_kwargs(self):
        """Overloaded to add the company id to the kwargs so the selection can be filtered."""
        kwargs = super(ComponentCreateView, self).get_form_kwargs()
        kwargs['company_id'] = self.kwargs.get('company_id')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ComponentCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "component"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # Add the reference to the proper contract to the contract.
        contract_id = self.kwargs.get('contract_id')
        form.set_contract(contract_id)

        form.finalize_creation(contract_id)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ComponentUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ComponentForm
    extra_context = {'object_type': "component"}

    def get_form_kwargs(self):
        """Overloaded to add the company id to the kwargs so the selection can be filtered."""
        kwargs = super(ComponentUpdateView, self).get_form_kwargs()
        kwargs['company_id'] = self.kwargs.get('company_id')
        return kwargs

    def get_object(self, queryset=Component.objects.all()):
        id_ = self.kwargs.get('component_id')
        return get_object_or_404(Component, component_id=id_)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ComponentDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(ComponentDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "component"
        context['list_page'] = ["contract_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=Component.objects.all()):
        id_ = self.kwargs.get('component_id')
        return get_object_or_404(Component, component_id=id_)

    def get_success_url(self):
        return reverse('contract_list', args=[self.kwargs.get('company_id')])
