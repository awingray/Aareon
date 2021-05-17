from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from InvoiceEngineApp.forms import ContractPersonFormSet
from InvoiceEngineApp.models import ContractPerson


@login_required
def contract_person_update_view(request, company_id, contract_id):
    FormSet = modelformset_factory(
        ContractPerson,
        exclude=('contract', 'tenancy'),
        formset=ContractPersonFormSet,
        extra=1,
        can_delete=True
    )

    queryset = ContractPerson.objects.filter(
        contract_id=contract_id
    )

    if request.method == 'POST':
        formset = FormSet(request.POST, request.FILES, queryset=queryset)
        if formset.is_valid():
            for form in formset.forms:
                form.instance.contract_id = contract_id
                form.instance.tenancy_id = company_id
            formset.save()

            return HttpResponseRedirect(
                reverse(
                    "contract_details",
                    args=[
                        company_id,
                        contract_id
                    ]
                )
            )
    else:
        formset = FormSet(queryset=queryset)

    context = {
        'formset': formset,
        'company_id': company_id,
        'contract_id': contract_id
    }

    return render(
        request, 'InvoiceEngineApp/manage_contract_persons.html', context
    )
