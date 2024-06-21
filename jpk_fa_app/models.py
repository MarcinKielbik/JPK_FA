from django.db import models

class Item(models.Model):
    net_price = models.FloatField()
    # Field for the net price of the item.

    gross_price = models.FloatField()
    # Field for the gross price of the item.

    name = models.CharField(max_length=255, null=True, blank=True)
    # Field for the name of the item. Can be null and blank.

class Invoice(models.Model):
    country = models.CharField(max_length=255)
    # Field for the country of origin for the invoice.

    vat = models.CharField(max_length=10)
    # Field for the VAT rate of the invoice.

    position = models.ManyToManyField(Item)
    # Many-to-many relationship with Item model for the positions on the invoice.

class JPK_FA(models.Model):
    version_diagram = models.CharField(max_length=10)
    # Field for the version diagram of the JPK_FA file.

    invoice = models.ManyToManyField(Invoice)
    # Many-to-many relationship with Invoice model for the invoices in the JPK_FA file.
