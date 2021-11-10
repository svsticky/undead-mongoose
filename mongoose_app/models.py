from typing import Any, Dict, Tuple
from django.db import models
from django.utils.html import mark_safe
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=30)
    price = models.FloatField()
    image = models.ImageField()
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

    def euro(self):
        return "€{:0.2f}".format(self.price)
    
    def image_view(self):
        if self.image:
            return mark_safe('<img src="{}" width="100" height="100"/>'.format(self.image.url))
        else:
            return ""
    image_view.short_description = 'Image View'
    image_view.allow_tags = True

    # Deletes image on removing the product
    def delete(self, using: Any = None, keep_parents: bool = False) -> Tuple[int, Dict[str, int]]:
        self.image.storage.delete(self.image.name)
        return super().delete(using=using, keep_parents=keep_parents)

class ProductTransactions(models.Model):
    product_id = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
    )
    transaction_id = models.ForeignKey(
        'Transaction',
        on_delete=models.CASCADE,
    )
    product_price = models.FloatField()
    amount = models.IntegerField()

class Transaction(models.Model):
    user_id = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    transaction_id = models.CharField(max_length=30)
    transaction_sum = models.FloatField()
    date = models.DateField(auto_now=True)

    def __str__(self):
        return 'Transaction: ' + str(self.transaction_id)

class User(models.Model):
    user_id = models.CharField(max_length=30)
    balance = models.FloatField()

    def __str__(self):
        return 'User: ' + self.user_id

class Cards(models.Model):
    card_id = models.CharField(max_length=8)
    active = models.BooleanField()
    user_id = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
