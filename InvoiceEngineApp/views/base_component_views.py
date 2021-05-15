from django.http import Http404
from django.shortcuts import get_object_or_404

from InvoiceEngineApp.forms import BaseComponentForm
from InvoiceEngineApp.models import BaseComponent
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
    ParentDetailView
)


class BaseComponentListView(ParentListView):
    template_name = 'InvoiceEngineApp/base_component_list.html'
    model = BaseComponent


class BaseComponentCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    form_class = BaseComponentForm

    def __init__(self):
        super().__init__()
        self.object_type = "base component"
        self.list_page = "base_component_list"

    def form_valid(self, form):
        self.object = form.instance
        self.object.create(self.tenancy)
        return super().form_valid(form)


class BaseComponentUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    form_class = BaseComponentForm

    def __init__(self):
        super().__init__()
        self.object_type = "base component"
        self.list_page = "base_component_list"

    def get_object(self, queryset=BaseComponent.objects.all()):
        base_component_id = self.kwargs.get('base_component_id')
        qs = queryset.filter(base_component_id=base_component_id)
        qs = super().filter_by_tenancy(qs)
        base_component = get_object_or_404(qs)

        if not base_component.can_update_or_delete():
            raise Http404('No base component matches the given query.')
        return base_component


class BaseComponentDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "base component"
        self.list_page = "base_component_list"

    def get_object(self, queryset=BaseComponent.objects.all()):
        base_component_id = self.kwargs.get('base_component_id')
        qs = queryset.filter(base_component_id=base_component_id)
        qs = super().filter_by_tenancy(qs)
        base_component = get_object_or_404(qs)

        if not base_component.can_update_or_delete():
            raise Http404('No base component matches the given query.')
        return base_component
