"""
Views for the images app (list, add, edit, delete).

All views require login. File upload uses multipart/form-data.
Delete removes the record and the file from disk.
"""

import os

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ImageForm
from .models import Image


@login_required
def image_list(request):
    """List all images (name, URL, optional preview, actions)."""
    images = Image.objects.all().order_by("name")
    return render(request, "images/image_list.html", {"image_list": images})


@login_required
def image_add(request):
    """Show form to add an image; on valid POST create and store file."""
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Image added.")
            return redirect("images:image_list")
    else:
        form = ImageForm()
    return render(request, "images/image_form.html", {"form": form, "image": None, "is_edit": False})


@login_required
def image_edit(request, pk):
    """Show form to edit image; display current image and read-only URL; optional replacement file."""
    image = get_object_or_404(Image, pk=pk)
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            # If no new file was provided, keep the existing file
            if not request.FILES.get("file") and image.file:
                form.instance.file = image.file
            form.save()
            messages.success(request, "Image updated.")
            return redirect("images:image_list")
    else:
        form = ImageForm(instance=image)
    return render(
        request,
        "images/image_form.html",
        {"form": form, "image": image, "is_edit": True},
    )


@login_required
def image_delete_confirm(request, pk):
    """GET: show confirmation page. POST: delete image and file from disk, redirect to list."""
    image = get_object_or_404(Image, pk=pk)
    if request.method == "POST":
        # Delete file from disk before deleting the record (when using default filesystem storage)
        if image.file:
            path = getattr(image.file, "path", None)
            if path and os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        image.delete()
        messages.success(request, "Image deleted.")
        return redirect("images:image_list")
    return render(request, "images/image_confirm_delete.html", {"image": image})
