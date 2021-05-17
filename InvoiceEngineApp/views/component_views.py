from InvoiceEngineApp.forms import ComponentForm
from InvoiceEngineApp.models import Component
from InvoiceEngineApp.views.parent_views import (
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView
)


class ComponentCreateView(ParentCreateView):
    form_class = ComponentForm
    list_page = "contract_details"

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of base components & VAT rates
        based on the tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.kwargs.get('company_id'))
        return form


class ComponentUpdateView(ParentUpdateView):
    """A component can only be updated when it has not been invoiced yet."""
    model = Component
    form_class = ComponentForm
    list_page = "contract_details"
    pk_url_kwarg = 'component_id'
    is_contract = True

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.object.tenancy)
        return form

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.remove_from_contract()
        return obj

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the
        form.
        """
        self.object = form.save(commit=False)
        self.object.update()
        return super().form_valid(form)


class ComponentDeleteView(ParentDeleteView):
    """A component can only be deleted when it has not been invoiced yet."""
    model = Component
    list_page = "contract_details"
    success_page = "contract_details"
    pk_url_kwarg = 'component_id'
    is_contract = True
