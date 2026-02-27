"""
Contact model for the lease app.

Stores contact info: first name, middle name (optional), last name, email, phone.
Persistence is in the project's SQLite database via Django ORM.
"""

from django.db import models


class Contact(models.Model):
    """
    A contact (e.g. lessee or prospect) in the lease app.
    """

    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    phone_number = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def __str__(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p).strip() or "(no name)"
