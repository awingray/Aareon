from django.contrib import admin
from django.urls import path, include
from InvoiceEngineApp.views.general_views import *
from InvoiceEngineApp.views.tenancy_views import *
from InvoiceEngineApp.views.contract_type_views import *
from InvoiceEngineApp.views.base_component_views import *
from InvoiceEngineApp.views.vat_rate_views import *


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

    # contract type pages.
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

    # base component pages.
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
]
