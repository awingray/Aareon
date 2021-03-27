from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView
)
from InvoiceEngineApp.models import Tenancy
from InvoiceEngineApp.forms import TenancyFrom


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyListView(ListView):
    """Show the user a list of all tenancies available to them."""
    template_name = 'InvoiceEngineApp/tenancy_list.html'

    def invoice_contracts(self, company_id):
        # This function is for testing the invoice engine!
        tenancy = get_object_or_404(Tenancy, company_id=company_id)
        tenancy.invoice_contracts()
        return HttpResponse("Invoicing started!")

    def get_queryset(self):
        # The user should only see the tenancy objects associated with themselves.
        return Tenancy.objects.filter(tenancy_id=self.request.user.username)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyCreateView(CreateView):
    """Allow the user to fill in a form to create a new tenancy."""
    template_name = 'InvoiceEngineApp/create.html'
    form_class = TenancyFrom
    extra_context = {'object_type': "tenancy", 'list_page': ["tenancy_list"]}

    def form_valid(self, form):
        # Save the user id as the tenancy_id.
        form.instance.tenancy_id = self.request.user.username
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tenancy_list')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyDetailView(DetailView):
    """Show the user the details corresponding to a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """
    template_name = 'InvoiceEngineApp/details.html'
    extra_context = {'object_type': "tenancy", 'list_page': ["tenancy_list"]}

    def get_object(self, queryset=Tenancy.objects.all()):
        id_ = self.kwargs.get('company_id')
        return get_object_or_404(Tenancy, company_id=id_)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyUpdateView(UpdateView):
    """Allow the user to change a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """
    template_name = 'InvoiceEngineApp/update.html'
    form_class = TenancyFrom
    extra_context = {'object_type': "tenancy"}

    def get_object(self, queryset=Tenancy.objects.all()):
        id_ = self.kwargs.get('company_id')
        return get_object_or_404(Tenancy, company_id=id_)

    def get_success_url(self):
        return reverse('tenancy_list')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyDeleteView(DeleteView):
    """Allow the user to delete a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """
    template_name = 'InvoiceEngineApp/delete.html'
    extra_context = {'object_type': "tenancy", 'list_page': ["tenancy_list"]}

    def get_object(self, queryset=Tenancy.objects.all()):
        id_ = self.kwargs.get('company_id')
        return get_object_or_404(Tenancy, company_id=id_)

    def get_success_url(self):
        return reverse('tenancy_list')
