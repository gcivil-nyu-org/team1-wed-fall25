from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import SignupForm, EmailOrUsernameAuthenticationForm


class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Account created. You can now log in.")
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


def logout_view(request):
    """Handle both GET and POST logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("accounts:login")
