from django.shortcuts import get_object_or_404

# from InvoiceEngineApp.forms import
from InvoiceEngineApp.models import GeneralLedgerPost
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
    ParentDetailView
)


class GLPostListView(ParentListView):
    template_name = 'InvoiceEngineApp/glpost_list.html'
    model = GeneralLedgerPost


class GLPostCreateView(ParentCreateView):
    template_name = 'InvoiceEngineApp/create.html'
    #form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.object_type = "GL Post"
        self.list_page = "glpost_list"


class GLPostDetailView(ParentDetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def __init__(self):
        super().__init__()
        self.object_type = "GL Post"
        self.list_page = "glpost_list"

    def get_object(self, queryset=GeneralLedgerPost.objects.all()):
        general_ledger_post_id = self.kwargs.get('general_ledger_post_id')
        qs = queryset.filter(general_ledger_post_id=general_ledger_post_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class GLPostUpdateView(ParentUpdateView):
    template_name = 'InvoiceEngineApp/update.html'
    #form_class = VATRateForm

    def __init__(self):
        super().__init__()
        self.object_type = "GL Post"
        self.list_page = "glpost_list"

    def get_object(self, queryset=GeneralLedgerPost.objects.all()):
        general_ledger_post_id = self.kwargs.get('general_ledger_post_id')
        qs = queryset.filter(general_ledger_post_id=general_ledger_post_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)


class GLPostDeleteView(ParentDeleteView):
    template_name = 'InvoiceEngineApp/delete.html'

    def __init__(self):
        super().__init__()
        self.object_type = "GL Post"
        self.list_page = "glpost_list"

    def get_object(self, queryset=GeneralLedgerPost.objects.all()):
        general_ledger_post_id = self.kwargs.get('general_ledger_post_id')
        qs = queryset.filter(general_ledger_post_id=general_ledger_post_id)
        qs = super().filter_by_tenancy(qs)
        return get_object_or_404(qs)
