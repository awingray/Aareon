from django.contrib.auth.decorators import login_required
from django.db.models import query_utils
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView,
)
from InvoiceEngineApp.models import Tenancy, Collection
from InvoiceEngineApp.forms import TenancyAdministratorForm, TenancySubscriberForm

import csv

"""     example export function

Name: Name from cpers
Adress: Address from cpers
City: City from cpers
Payment method: Pay_meth from cpers
Payment day: Pay_day from cpers
Invoice number: Inv_nr  from inv
Invoice date: Inv_date from inv
**Contract ID: Contr_id from cpers
Invoice ID: Inv_id from inv
***Invoice amount: Inv_amt from invinc
Mandate: Mandaat form cpers
IBAN: Iban form cpers
Email: Email form cpers
Phone: Phone from cpers*

** is it contract id or contract person id?

*** invoice amount == total_amount?

 """


def output(request, company_id, queryset=Collection.objects.all()):
    response = HttpResponse(content_type="text/csv")
    response["pipContent-Disposition"] = 'attachment; filename="output.csv"'

    ### filtering the contracts for the tenant
    """     qs = queryset.filter(
        tenancy__company_id=company_id, tenancy__tenancy_id=request.user.username
    ) """
    # Retrieve the set for contract persons and invoices from the corresonding contract
    # print(cpers, invs)
    qs = queryset
    print(qs)
    writer = csv.writer(response)
    # Use exclude to omit the fields instead of manually define the field names - Awin
    fields = [
        "name",
        "address",
        "city",
        "payment_method",
        "payment_day",
        "invoice_number",
        "date",
        "contract_person_id",
        "invoice_id",
        "total_amount",
        "mandate",
        "iban",
        "email",
    ]

    writer.writerow(fields)
    # print(qs)
    for obj in qs:

        cpers = obj.get_contract_persons()
        invs = obj.get_invoices()

        """         val = [
            cpers.name,
            cpers.address,
            cpers.city,
            cpers.payment_method,
            cpers.payment_day,
            invs.invoice_number,
            invs.date,
            cpers.contract_person_id,
            invs.invoice_id,
            invs.total_amount,
            cpers.mandate,
            cpers.iban,
            cpers.email,
        ] """
        val = []

        writer.writerow(val)

    return response


@method_decorator(login_required(login_url="/login/"), name="dispatch")
class TenancyListView(ListView):
    """Show the user a list of all tenancies available to them."""

    model = Tenancy
    paginate_by = 10

    def invoice_contracts(self, company_id):
        # This function is for testing the invoice engine!
        tenancy = get_object_or_404(
            Tenancy.objects.filter(
                company_id=company_id,
            )
        )
        tenancy.invoice_contracts()
        return HttpResponse("Invoicing started!")

    def get_template_names(self):
        # super().get_template_names()
        if self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            return ["InvoiceEngineApp/tenancy_list_administrator.html"]
        return ["InvoiceEngineApp/tenancy_list.html"]

    def get_queryset(self):
        # The user should only see the tenancy objects associated with themselves.
        qs = super().get_queryset()
        if self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            return qs

        return qs.filter(tenancy_id=self.request.user.username)


@method_decorator(login_required(login_url="/login/"), name="dispatch")
class TenancyCreateView(CreateView):
    """Allow the user to fill in a form to create a new tenancy."""

    template_name = "InvoiceEngineApp/create.html"
    form_class = TenancyAdministratorForm
    extra_context = {"object_type": "tenancy", "list_page": ["tenancy_list"]}

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            raise Http404("No Tenancy matches the given query.")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("tenancy_list")


@method_decorator(login_required(login_url="/login/"), name="dispatch")
class TenancyDetailView(DetailView):
    """Show the user the details corresponding to a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """

    template_name = "InvoiceEngineApp/details.html"
    extra_context = {"object_type": "tenancy", "list_page": ["tenancy_list"]}

    def get_object(self, queryset=Tenancy.objects.all()):
        qs = Tenancy.objects.filter(company_id=self.kwargs.get("company_id"))
        if self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            return get_object_or_404(qs)

        return get_object_or_404(qs.filter(tenancy_id=self.request.user.username))


@method_decorator(login_required(login_url="/login/"), name="dispatch")
class TenancyUpdateView(UpdateView):
    """Allow the user to change a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """

    template_name = "InvoiceEngineApp/update.html"
    extra_context = {"object_type": "tenancy"}

    def get_form_class(self):
        if self.request.user.has_perm("add_tenancy"):
            return TenancyAdministratorForm
        return TenancySubscriberForm

    def get_object(self, queryset=Tenancy.objects.all()):
        qs = Tenancy.objects.filter(company_id=self.kwargs.get("company_id"))
        if self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            return get_object_or_404(qs)

        return get_object_or_404(qs.filter(tenancy_id=self.request.user.username))

    def get_success_url(self):
        return reverse("tenancy_list")


@method_decorator(login_required(login_url="/login/"), name="dispatch")
class TenancyDeleteView(DeleteView):
    """Allow the user to delete a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """

    template_name = "InvoiceEngineApp/delete.html"
    extra_context = {"object_type": "tenancy", "list_page": ["tenancy_list"]}

    def get_object(self, queryset=Tenancy.objects.all()):
        if not self.request.user.has_perm("InvoiceEngineApp.add_tenancy"):
            raise Http404("No Tenancy matches the given query.")

        return get_object_or_404(
            Tenancy.objects.filter(company_id=self.kwargs.get("company_id"))
        )

    def get_success_url(self):
        return reverse("tenancy_list")
