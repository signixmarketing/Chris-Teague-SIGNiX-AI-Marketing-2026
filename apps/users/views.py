"""
Profile and auth-related views for lease officers.

- root_redirect: send / to /profile/ or login.
- profile_view: read-only profile (with Edit button).
- profile_edit: form to update profile; redirects to profile_view on success.
- health: simple 200 + JSON for tunnel/sanity checks (e.g. scripts/verify_ngrok.sh).
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages

from .forms import LeaseOfficerProfileEditForm
from .models import LeaseOfficerProfile


def health(request):
    """Return 200 and {"status": "ok"} for tunnel/sanity checks (no auth required)."""
    return JsonResponse({"status": "ok"})


def root_redirect(request):
    """Send authenticated users to profile, others to login."""
    if request.user.is_authenticated:
        return redirect("users:profile")
    return redirect("login")


@login_required
def profile_view(request):
    """Display the current user's lease officer profile (read-only)."""
    profile = get_object_or_404(LeaseOfficerProfile, user=request.user)
    return render(request, "users/profile_view.html", {"profile": profile})


@login_required
def profile_edit(request):
    """Display and process the profile edit form; redirect to profile on success."""
    profile = get_object_or_404(LeaseOfficerProfile, user=request.user)
    if request.method == "POST":
        form = LeaseOfficerProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("users:profile")
    else:
        form = LeaseOfficerProfileEditForm(instance=profile)
    return render(request, "users/profile_edit.html", {"form": form})
