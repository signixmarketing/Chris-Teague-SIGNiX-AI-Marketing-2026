"""
Views for the contacts app (list, add, edit, delete).

All views require login. Delete uses GET for confirmation page and POST to perform delete.
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
from .models import Contact


@login_required
def contact_list(request):
    """List all contacts in a table (First Name, Middle Name, Last Name, Email, Phone, Actions)."""
    contacts = Contact.objects.all().order_by("last_name", "first_name")
    return render(request, "contacts/contact_list.html", {"contact_list": contacts})


@login_required
def contact_add(request):
    """Show form to add a contact; on valid POST create and redirect to list."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact added.")
            return redirect("contacts:contact_list")
    else:
        form = ContactForm()
    return render(request, "contacts/contact_form.html", {"form": form, "is_edit": False})


@login_required
def contact_edit(request, pk):
    """Show form to edit a contact; on valid POST update and redirect to list."""
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated.")
            return redirect("contacts:contact_list")
    else:
        form = ContactForm(instance=contact)
    return render(
        request,
        "contacts/contact_form.html",
        {"form": form, "contact": contact, "is_edit": True},
    )


@login_required
def contact_delete_confirm(request, pk):
    """GET: show confirmation page. POST: delete contact and redirect to list."""
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Contact deleted.")
        return redirect("contacts:contact_list")
    return render(request, "contacts/contact_confirm_delete.html", {"contact": contact})
