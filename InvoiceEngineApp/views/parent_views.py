from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView
)

from InvoiceEngineApp.models import Tenancy


class ParentListView(LoginRequiredMixin, ListView):
    """This class defines common methods of ListViews used in this project."""
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'
    paginate_by = 10

    def filter_by_tenancy(self, qs_to_filter):
        """Filter the full queryset by tenancy.  This method also makes sure that someone without access to the tenancy
        cannot view the page.
        """
        # The user will not know if a tenancy with this company_id exists in the database.
        # They will just know that they cannot find a tenancy with that company_id.
        tenancy = get_object_or_404(
            Tenancy,
            company_id=self.kwargs.get('company_id'),
            tenancy_id=self.request.user.username
        )

        return qs_to_filter.filter(tenancy=tenancy)

    def get_queryset(self):
        """Overload the get_queryset method to filter by tenancy."""
        qs = super().get_queryset()
        return self.filter_by_tenancy(qs)

    def get_context_data(self, **kwargs):
        """Add information to send to the HTML environment."""
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        context['company_id'] = self.kwargs.get('company_id')  # Needed to link to other pages with company_id in URL.
        return context


class ParentCreateView(LoginRequiredMixin, CreateView):
    """This class defines common methods of CreateViews used in this project."""
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'

    def __init__(self):
        super().__init__()
        self.object_type = None
        self.list_page = None
        self.tenancy = None

    def dispatch(self, request, *args, **kwargs):
        """"Perform a check whether this user has access to this tenancy. If so, save the tenancy for later use."""
        self.tenancy = get_object_or_404(
            Tenancy,
            company_id=self.kwargs.get('company_id'),
            tenancy_id=self.request.user.username
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add information to send to the HTML environment."""
        context = super().get_context_data(**kwargs)
        context['object_type'] = self.object_type
        context['list_page'] = [
            self.list_page,
            self.kwargs.get('company_id')
        ]
        return context

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the form."""
        form.finalize_creation(self)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            self.list_page,
            args=[self.kwargs.get('company_id')]
        )


class ParentDetailView(LoginRequiredMixin, DetailView):
    """This class defines common methods of UpdateViews used in this project."""
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'

    def __init__(self):
        super().__init__()
        self.object_type = None
        self.list_page = None

    def filter_by_tenancy(self, queryset):
        return queryset.filter(tenancy__tenancy_id=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_type'] = self.object_type
        context['list_page'] = [
            self.list_page,
            self.kwargs.get('company_id')
        ]
        return context


class ParentUpdateView(LoginRequiredMixin, UpdateView):
    """This class defines common methods of UpdateViews used in this project."""
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'

    def __init__(self):
        super().__init__()
        self.object_type = None
        self.list_page = None

    def filter_by_tenancy(self, queryset):
        return queryset.filter(tenancy__tenancy_id=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_type'] = self.object_type
        return context

    def get_success_url(self):
        return reverse(self.list_page, args=[self.kwargs.get('company_id')])


class ParentDeleteView(LoginRequiredMixin, DeleteView):
    """This class defines common methods of DeleteViews used in this project."""
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'

    def __init__(self):
        super().__init__()
        self.object_type = None
        self.list_page = None

    def filter_by_tenancy(self, queryset):
        return queryset.filter(tenancy__tenancy_id=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_type'] = self.object_type
        context['list_page'] = [
            self.list_page,
            self.kwargs.get('company_id')
        ]
        return context

    def get_success_url(self):
        return reverse(self.list_page, args=[self.kwargs.get('company_id')])
