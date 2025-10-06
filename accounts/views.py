from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import SignupForm, EmailOrUsernameAuthenticationForm, UserProfileForm
from .models import UserProfile


class SignupView(FormView):
    template_name = 'accounts/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Account created. You can now log in.')
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


def logout_view(request):
    """Handle both GET and POST logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """View user profile"""
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})
