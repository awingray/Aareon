from django.urls import path
from InvoiceEngineApp.views.general_views import *
from InvoiceEngineApp.views.tenancy_views import *
from InvoiceEngineApp.views.contract_type_views import *
from InvoiceEngineApp.views.base_component_views import *
from InvoiceEngineApp.views.vat_rate_views import *
from InvoiceEngineApp.views.contract_views import *
from InvoiceEngineApp.views.component_views import *
from InvoiceEngineApp.views.contract_person_views import *
from InvoiceEngineApp.views.invoice_views import *


urlpatterns = [
    # General pages.
    path('', HomePage.as_view()),
    path('profile/', UserProfilePage.as_view(), name='profile'),

    # Tenancy pages.
    path('profile/tenancies/', TenancyListView.as_view(), name='tenancy_list'),
    path('profile/tenancies/create/', TenancyCreateView.as_view(), name='tenancy_create'),
    path('profile/tenancies/<int:company_id>/', TenancyDetailView.as_view(), name='tenancy_details'),
    path('profile/tenancies/<int:company_id>/update/', TenancyUpdateView.as_view(), name='tenancy_update'),
    path('profile/tenancies/<int:company_id>/delete/', TenancyDeleteView.as_view(), name='tenancy_delete'),

    # This path is for testing the invoice_contracts button!
    path('profile/tenancies/<int:company_id>/run_engine/',
         TenancyListView.invoice_contracts,
         name='invoice_contracts'
         ),

    # Contract type pages.
    path('profile/tenancies/<int:company_id>/contract_types/',
         ContractTypeListView.as_view(),
         name='contract_type_list'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/create/',
         ContractTypeCreateView.as_view(),
         name='contract_type_create'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/',
         ContractTypeDetailView.as_view(),
         name='contract_type_details'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/update/',
         ContractTypeUpdateView.as_view(),
         name='contract_type_update'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/delete/',
         ContractTypeDeleteView.as_view(),
         name='contract_type_delete'
         ),

    # Base component pages.
    path('profile/tenancies/<int:company_id>/base_components/',
         BaseComponentListView.as_view(),
         name='base_component_list'
         ),
    path('profile/tenancies/<int:company_id>/base_components/create/',
         BaseComponentCreateView.as_view(),
         name='base_component_create'
         ),
    path('profile/tenancies/<int:company_id>/base_components/<int:base_component_id>/',
         BaseComponentDetailView.as_view(),
         name='base_component_details'
         ),
    path('profile/tenancies/<int:company_id>/base_components/<int:base_component_id>/update/',
         BaseComponentUpdateView.as_view(),
         name='base_component_update'
         ),
    path('profile/tenancies/<int:company_id>/base_components/<int:base_component_id>/delete/',
         BaseComponentDeleteView.as_view(),
         name='base_component_delete'
         ),

    # VAT rate pages.
    path('profile/tenancies/<int:company_id>/vat_rates/',
         VATRateListView.as_view(),
         name='vat_rate_list'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/create/',
         VATRateCreateView.as_view(),
         name='vat_rate_create'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/<int:vat_rate_id>/',
         VATRateDetailView.as_view(),
         name='vat_rate_details'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/<int:vat_rate_id>/update/',
         VATRateUpdateView.as_view(),
         name='vat_rate_update'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/<int:vat_rate_id>/delete/',
         VATRateDeleteView.as_view(),
         name='vat_rate_delete'
         ),

    # Contract pages.
    path('profile/tenancies/<int:company_id>/contracts/',
         ContractListView.as_view(),
         name='contract_list'
         ),
    path('profile/tenancies/<int:company_id>/contracts/create/',
         ContractCreateView.as_view(),
         name='contract_create'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/',
         ContractDetailView.as_view(),
         name='contract_details'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/update/',
         ContractUpdateView.as_view(),
         name='contract_update'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/delete/',
         ContractDeleteView.as_view(),
         name='contract_delete'
         ),

    # Component pages.
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/create/',
         ComponentCreateView.as_view(),
         name='component_create'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/<int:component_id>/update/',
         ComponentUpdateView.as_view(),
         name='component_update'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/<int:component_id>/delete/',
         ComponentDeleteView.as_view(),
         name='component_delete'
         ),

    # Contract person pages.
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/contract_person/create/',
         ContractPersonCreateView.as_view(),
         name='contract_person_create'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/contract_person/<int:contract_person_id>/update/',
         ContractPersonUpdateView.as_view(),
         name='contract_person_update'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/contract_person/<int:contract_person_id>/delete/',
         ContractPersonDeleteView.as_view(),
         name='contract_person_delete'
         ),

    # Invoice pages.
    path('profile/tenancies/<int:company_id>/invoices/',
         InvoiceListView.as_view(),
         name='invoice_list'
         ),
    path('profile/tenancies/<int:company_id>/invoices/<int:invoice_id>',
         InvoiceDetailView.as_view(),
         name='invoice_details'
         ),
]
