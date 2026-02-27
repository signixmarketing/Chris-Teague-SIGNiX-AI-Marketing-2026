"""
Vehicle model for the lease app.

Stores jet pack (and other vehicle) catalog data: sku, year, jpin.
Persistence is in the project's SQLite database via Django ORM.
"""

from django.db import models


class Vehicle(models.Model):
    """
    A vehicle (e.g. jet pack) available for leasing.

    Identified by sku and jpin; year stored as string to match seed data format.
    """

    sku = models.CharField(max_length=200)
    year = models.CharField(max_length=10)
    jpin = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return f"{self.sku} ({self.year})"
