from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from InvoiceEngineApp.models import Invoice, Tenancy


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class InvoiceListView(ListView):
    template_name = 'InvoiceEngineApp/invoice_list.html'

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        return Invoice.objects.filter(contract__tenancy=get_object_or_404(
                Tenancy,
                tenancy_id=self.request.user.username,
                company_id=company_id
            )
        )

    def get(self, request, *args, **kwargs):
        context = {'invoice_list': self.get_queryset(),
                   'company_id': self.kwargs.get('company_id')
                   }
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class InvoiceDetailView(DetailView):
    template_name = 'InvoiceEngineApp/details.html'

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        context['object_type'] = "invoice"
        context['list_page'] = ["invoice_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=Invoice.objects.all()):
        invoice_id = self.kwargs.get('invoice_id')
        return get_object_or_404(
            Invoice,
            contract__tenancy__tenancy_id=self.request.user.username,
            invoice_id=invoice_id
        )
