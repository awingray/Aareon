from django.contrib import admin
from django.urls import path, include
import InvoiceEngineApp.views.tenancy_views as tviews
import InvoiceEngineApp.views.general_views as gviews


urlpatterns = [
    path('', gviews.HomePage.as_view()),
    path('profile/', gviews.UserProfilePage.as_view(), name='profile'),
    path('profile/tenancies/', tviews.TenancyListView.as_view(), name='tenancy_list'),
    path('profile/tenancies/create/', tviews.TenancyCreateView.as_view(), name='tenancy_create'),
    path('profile/tenancies/<int:id>/', tviews.TenancyDetailView.as_view(), name='tenancy_details'),
    path('profile/tenancies/<int:id>/update/', tviews.TenancyUpdateView.as_view(), name='tenancy_update'),
    path('profile/tenancies/<int:id>/delete/', tviews.TenancyDeleteView.as_view(), name='tenancy_delete'),
]
