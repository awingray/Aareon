from django.contrib import admin
from django.urls import path, include
import InvoiceEngineApp.views.tenancy_views as tviews
import InvoiceEngineApp.views.general_views as gviews
import InvoiceEngineApp.views.contract_type_views as ctviews


urlpatterns = [
    # General pages.
    path('', gviews.HomePage.as_view()),
    path('profile/', gviews.UserProfilePage.as_view(), name='profile'),

    # Tenancy pages.
    path('profile/tenancies/', tviews.TenancyListView.as_view(), name='tenancy_list'),
    path('profile/tenancies/create/', tviews.TenancyCreateView.as_view(), name='tenancy_create'),
    path('profile/tenancies/<int:company_id>/', tviews.TenancyDetailView.as_view(), name='tenancy_details'),
    path('profile/tenancies/<int:company_id>/update/', tviews.TenancyUpdateView.as_view(), name='tenancy_update'),
    path('profile/tenancies/<int:company_id>/delete/', tviews.TenancyDeleteView.as_view(), name='tenancy_delete'),

    # contract type pages.
    path('profile/tenancies/<int:company_id>/contract_types/',
         ctviews.ContractTypeListView.as_view(),
         name='contract_type_list'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/create/',
         ctviews.ContractTypeCreateView.as_view(),
         name='contract_type_create'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/',
         ctviews.ContractTypeDetailView.as_view(),
         name='contract_type_details'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/update/',
         ctviews.ContractTypeUpdateView.as_view(),
         name='contract_type_update'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/delete/',
         ctviews.ContractTypeDeleteView.as_view(),
         name='contract_type_delete'
         )
]
