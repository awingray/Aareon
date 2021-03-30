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
from InvoiceEngineApp.models import BaseComponent, Tenancy
from InvoiceEngineApp.forms import BaseComponentForm


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class BaseComponentListView(ListView):
    template_name = 'InvoiceEngineApp/base_component_list.html'

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        return BaseComponent.objects.filter(
            tenancy=get_object_or_404(
                Tenancy,
                tenancy_id=self.request.user.username,
                company_id=company_id
            )
        )

    def get(self, request, *args, **kwargs):
        context = {'object_list': self.get_queryset(), 'company_id': self.kwargs.get('company_id')}
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class BaseComponentCreateView(CreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = BaseComponentForm

    def get_context_data(self, **kwargs):
        context = super(BaseComponentCreateView, self).get_context_data(**kwargs)
        context['object_type'] = "base component"
        context['list_page'] = ["base_component_list", self.kwargs.get('company_id')]
        return context

    def form_valid(self, form):
        # Add the reference to the proper tenancy to the base component.
        company_id = self.kwargs.get('company_id')
        form.set_tenancy(company_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('base_component_list', args=[self.kwargs.get('company_id')])

    def get(self, *args, **kwargs):
        get_object_or_404(Tenancy, company_id=self.kwargs.get('company_id'), tenancy_id=self.request.user.username)
        return super().get(*args, **kwargs)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class BaseComponentDetailView(DetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def get_context_data(self, **kwargs):
        context = super(BaseComponentDetailView, self).get_context_data(**kwargs)
        context['object_type'] = "base component"
        context['list_page'] = ["base_component_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=BaseComponent.objects.all()):
        base_component_id = self.kwargs.get('base_component_id')
        base_component = get_object_or_404(BaseComponent, tenancy__tenancy_id=self.request.user.username, base_component_id=base_component_id)
        return base_component


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class BaseComponentUpdateView(UpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = BaseComponentForm
    extra_context = {'object_type': "base component"}

    def get_object(self, queryset=BaseComponent.objects.all()):
        base_component_id = self.kwargs.get('base_component_id')
        base_component = get_object_or_404(BaseComponent, tenancy__tenancy_id=self.request.user.username, base_component_id=base_component_id)
        return base_component

    def get_success_url(self):
        return reverse('base_component_list', args=[self.kwargs.get('company_id')])


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class BaseComponentDeleteView(DeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(BaseComponentDeleteView, self).get_context_data(**kwargs)
        context['object_type'] = "base component"
        context['list_page'] = ["base_component_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=BaseComponent.objects.all()):
        base_component_id = self.kwargs.get('base_component_id')
        base_component = get_object_or_404(BaseComponent, tenancy__tenancy_id=self.request.user.username, base_component_id=base_component_id)
        return base_component

    def get_success_url(self):
        return reverse('base_component_list', args=[self.kwargs.get('company_id')])
