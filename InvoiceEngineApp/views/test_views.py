from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from InvoiceEngineApp.models import Tenancy


class TenancyMixinView(ListView):
    """This class defines common methods of Views used in this project."""

    def get_tenancy(self):
        """Select the proper tenancy, and to check whether this tenancy is accessible to the current user.
        Do not tell the user if they do not have permission, so they do not know whether this tenancy exists or not.
        """
        tenancy = get_object_or_404(
            Tenancy.objects.filter(
                company_id=self.kwargs.get('company_id'),
                tenancy_id=self.request.user.username
            )
        )
        return tenancy

    def refine_queryset(self, qs_to_filter):
        """Filter the full queryset by tenancy."""
        return qs_to_filter.filter(tenancy=self.get_tenancy())

    def get_queryset(self):
        qs = super().get_queryset()
        return self.refine_queryset(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        context['company_id'] = self.kwargs.get('company_id')
        return context
