"""
Forms for the images app.

ImageForm: add/edit image (name + file). File is optional on edit.
"""

from django import forms

from .models import Image


class ImageForm(forms.ModelForm):
    """Form to create or update an image; file is required on add, optional on edit."""

    class Meta:
        model = Image
        fields = ["name", "file"]
        widgets = {
            "file": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["file"].required = False
