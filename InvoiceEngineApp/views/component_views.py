from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import ComponentForm
from InvoiceEngineApp.models import Component
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
        self.list_page = "contract_list"

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of base components & VAT rates based on the tenancy."""
        form = super().get_form()
        form.filter_selectors(self.tenancy)
        return form


class ComponentUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = ComponentForm

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_list"

    def get_object(self, queryset=Component.objects.all()):
        component_id = self.kwargs.get('component_id')
        qs = queryset.filter(component_id=component_id).select_related('contract')
        qs = super().filter_by_tenancy(qs)
        component = get_object_or_404(qs)

        # Remove the amounts of this component from the contract to later add updated values
        # Do not save the contract until the update is complete
        component.contract.base_amount -= component.base_amount
        component.contract.total_amount -= component.total_amount
        component.contract.vat_amount -= component.vat_amount

        return component

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the tenancy."""
        form = super().get_form()
        form.filter_selectors(self.object.tenancy)
        return form

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the form."""
        form.finalize_update()
        return super().form_valid(form)


class ComponentDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "component"
        self.list_page = "contract_list"

    def get_object(self, queryset=Component.objects.all()):
        component_id = self.kwargs.get('component_id')
        qs = queryset.filter(component_id=component_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
