from typing import Any, Dict, Iterable, Optional, Tuple
from django.db import models
from django.utils.html import mark_safe
from django.conf import settings
from decimal import Decimal
#from django.utils.translation import Trans

class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=30)
    price = models.DecimalField(decimal_places=2, max_digits=6)
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
        'SaleTransaction',
        on_delete=models.CASCADE,
    )
    product_price = models.DecimalField(decimal_places=2, max_digits=6)
    amount = models.IntegerField()


# Every transaction has at least a link with a user, an id and a sum
# Whether this sum has a negative or positive influence on the total credit depends on the type of transaction
class Transaction(models.Model):
    user_id = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    transaction_id = models.CharField(max_length=30)
    transaction_sum = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(auto_now=True)

    # Makes this class abstract which means that there won't be
    # a literal class for it in the database, do we want this?
    class Meta:
        abstract = True

    def __str__(self):
        return 'Transaction: ' + str(self.transaction_id)


# This transaction is created when a user buys products.
class SaleTransaction(Transaction):

    # A sale can be cancelled in which case it does not count towards the balance.
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return 'Sale: ' + str(self.transaction_id)


# This transaction is created when BESTUUUUUR tops up credit for a member.
class TopUpTransaction(Transaction):

    # Not sure about this. Could be an option.
    refunded = models.BooleanField(default=False)
    added = models.BooleanField(default=False)

    def __str__(self):
        return 'Top up: ' + str(self.transaction_id) + ": " + str(self.user_id.name)

    def save(self, force_insert: bool = False, force_update: bool = False, using: Optional[str] = None, update_fields: Optional[Iterable[str]] = None) -> None:
        if not self.added and not self.refunded:
            self.user_id.balance += self.transaction_sum
            self.user_id.save()
            self.added = True
        elif self.added and self.refunded:
            self.user_id.balance -= self.transaction_sum
            self.user_id.save()
            self.added = False
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
    
    def delete(self, using: Any = None, keep_parents: bool = False) -> Tuple[int, Dict[str, int]]:
        self.user_id.balance -= self.transaction_sum
        self.user_id.save()
        return super().delete(using=using, keep_parents=keep_parents)
    


# User needs name, age and balance to be able to make sense to BESTUUUUUR.
class User(models.Model):
    user_id = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    age = models.IntegerField()
    balance = models.DecimalField(decimal_places=2, max_digits=6, default=Decimal('0.00'))

    def __str__(self):
        return 'User: ' + self.name


class Cards(models.Model):
    card_id = models.CharField(max_length=8)
    active = models.BooleanField()
    user_id = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
