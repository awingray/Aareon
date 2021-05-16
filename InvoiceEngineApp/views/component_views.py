from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from InvoiceEngineApp.forms import ComponentForm, ComponentDeactivationForm
from InvoiceEngineApp.models import Component, Contract
from InvoiceEngineApp.views.parent_views import (
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView
)


class ComponentCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = ComponentForm

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_details"
        self.contract = None

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of base components & VAT rates
        based on the tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.tenancy)
        return form

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables, set the tenancy and the contract, and then check if
        it's valid.
        """
        self.object = None

        form = self.get_form()
        form.instance.set_tenancy_and_contract(
            self.tenancy, self.contract
        )

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """If all entries on the form are correct, finalize the component."""
        self.object = form.instance
        self.object.create()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.contract = get_object_or_404(
            Contract.objects.select_related('contract_type'),
            contract_id=self.kwargs.get('contract_id')
        )

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            self.list_page,
            args=[
                self.kwargs.get('company_id'),
                self.kwargs.get('contract_id')
            ]
        )


class ComponentUpdateView(ParentUpdateView):
    """A component can only be updated when it has not been invoiced yet."""
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ComponentForm

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_details"

    def get_object(self, queryset=Component.objects.all()):
        component_id = self.kwargs.get('component_id')
        qs = queryset.filter(component_id=component_id)
        qs = super().filter_by_tenancy(qs)
        component = get_object_or_404(qs.select_related('contract'))

        if not component.can_update_or_delete():
            # This component has been invoiced, so don't allow updates
            raise Http404("No Component matches the given query.")

        # Remove the amounts of this component from the contract to later
        # add updated values
        # Do not save the contract until the update is complete
        component.remove_from_contract()

        return component

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.object.tenancy)
        return form

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the
        form.
        """
        self.object.update()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            self.list_page,
            args=[
                self.kwargs.get('company_id'),
                self.kwargs.get('contract_id')
            ]
        )


class ComponentDeactivationView(ParentUpdateView):
    """A component can only be updated when it has not been invoiced yet."""
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ComponentDeactivationForm

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_details"

    def get_object(self, queryset=Component.objects.all()):
        component_id = self.kwargs.get('component_id')
        qs = queryset.filter(component_id=component_id)
        qs = super().filter_by_tenancy(qs)
        component = get_object_or_404(qs.select_related('contract'))

        if component.end_date or component.can_update_or_delete():
            raise Http404("No Component matches the given query.")

        return component

    def form_valid(self, form):
        self.object = form.instance
        self.object.deactivate()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            self.list_page,
            args=[
                self.kwargs.get('company_id'),
                self.kwargs.get('contract_id')
            ]
        )


class ComponentDeleteView(ParentDeleteView):
    """A component can only be deleted when it has not been invoiced yet."""
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_details"

    def get_object(self, queryset=Component.objects.all()):
        component_id = self.kwargs.get('component_id')
        qs = queryset.filter(component_id=component_id)
        qs = super().filter_by_tenancy(qs)
        component = get_object_or_404(qs.select_related('contract'))

        if not component.can_update_or_delete():
            # This component has been invoiced, so don't allow updates
            raise Http404("No Component matches the given query.")

        return component

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_page'] = [self.list_page,
                                self.kwargs.get('company_id'),
                                self.kwargs.get('contract_id')]
        return context

    def get_success_url(self):
        return reverse(
            self.list_page,
            args=[
                self.kwargs.get('company_id'),
                self.kwargs.get('contract_id')
            ]
        )
