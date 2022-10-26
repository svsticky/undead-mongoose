from typing import Any, Dict, Iterable, Optional, Tuple
from django.db import models
from django.utils.html import mark_safe
from django.conf import settings
from decimal import Decimal
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.defaultfilters import mark_safe


top_up_types = [
    (1, "Pin"),
    (2, "Credit card")
]


class Category(models.Model):
    name = models.CharField(max_length=30)
    alcoholic = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

    def serialize(self) -> dict:
        products = Product.objects.filter(category=self, enabled=True)
        return {
            'name': self.name,
            'products': [p.serialize() for p in products]
        }


class Product(models.Model):
    name = models.CharField(max_length=60)
    price = models.DecimalField(decimal_places=2, max_digits=6)
    image = models.ImageField(null=True, blank=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
    )
    vat = models.ForeignKey(
        'VAT',
        on_delete=models.CASCADE,
        verbose_name="BTW"
    )
    enabled = models.BooleanField(default=True)

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
        if self.image:
            self.image.storage.delete(self.image.name)
        return super().delete(using=using, keep_parents=keep_parents)

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'image_url': settings.BASE_URL + self.image.url
        }


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
    product_vat = models.IntegerField()
    amount = models.IntegerField()

    def show_vat(self):
        return str(self.product_vat) + "%"

    def show_price(self):
        return "€{:0.2f}".format(self.product_price)

    class Meta:
        verbose_name_plural = "Products"


# Every transaction has at least a link with a user, an id and a sum
# Whether this sum has a negative or positive influence on the total credit depends on the type of transaction
class Transaction(models.Model):
    user_id = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
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
    added = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return 'Sale ' + str(self.id) + ": " + str(self.user_id.name)
    
    def save(self, force_insert: bool = False, force_update: bool = False, using: Optional[str] = None, update_fields: Optional[Iterable[str]] = None) -> None:
        if not self.added and not self.cancelled:
            self.user_id.balance -= self.transaction_sum
            self.added = True
        elif self.added and self.cancelled:
            self.user_id.balance += self.transaction_sum
            self.added = False
        self.user_id.save()
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
    
    def serialize(self):
        return {
            'member_id': self.user_id.user_id,
            'name': self.user_id.name,
            'price': str(self.transaction_sum),
            'date': str(self.date)
        }


# This transaction is created when BESTUUUUUR tops up credit for a member.
class TopUpTransaction(Transaction):
    added = models.BooleanField(default=False)
    type = models.IntegerField(choices=top_up_types, default=1)

    def __str__(self):
        return 'Top up: ' + str(self.id) + ": " + str(self.user_id.name)

    def save(self, force_insert: bool = False, force_update: bool = False, using: Optional[str] = None, update_fields: Optional[Iterable[str]] = None) -> None:
        if not self.added:
            self.user_id.balance += self.transaction_sum
            self.user_id.save()
            self.added = True
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def delete(self, using: Any = None, keep_parents: bool = False) -> Tuple[int, Dict[str, int]]:
        self.user_id.balance -= self.transaction_sum
        self.user_id.save()
        return super().delete(using=using, keep_parents=keep_parents)


# User needs name, age and balance to be able to make sense to BESTUUUUUR.
class User(models.Model):
    user_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    birthday = models.DateField()
    balance = models.DecimalField(decimal_places=2, max_digits=6, default=Decimal('0.00'))

    def __str__(self):
        return self.name

    def euro_balance(self):
        return "€{:0.2f}".format(self.balance)

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'birthday': self.birthday,
            'balance': self.balance,
        }


class Card(models.Model):
    card_id = models.CharField(max_length=8)
    active = models.BooleanField()
    user_id = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )


class CardConfirmation(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    card = models.ForeignKey(
        'Card',
        on_delete=models.CASCADE,  
    )
    token = models.CharField(max_length=32)


class VAT(models.Model):
    percentage = models.IntegerField(
        validators=[
            MinValueValidator(limit_value=0, message="Percentage can't be lower than 0"),
            MaxValueValidator(limit_value=100, message="Percentage can't be higher than 100")
        ]
    )

    def __str__(self) -> str:
        return "BTW: " + self.percentage_view()

    def percentage_view(self):
        return str(self.percentage) + "%"

    class Meta:
        verbose_name = "BTW percentage"
        verbose_name_plural = "BTW percentages"


class ProductForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Suikerwafel', 'class': 'form-control'}),
                            label=mark_safe('<label class="form-label">Name</label>'))
    price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '15.15', 'class': 'form-control'}),
                            label=mark_safe('<label class="form-label">Price</label>'))
    image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False,
                            label=mark_safe('<label class="form-label">Image</label>'))
    vat = forms.ModelChoiceField(queryset=VAT.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}),
                            label=mark_safe('<label class="form-label">VAT</label>'))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}),
                            label=mark_safe('<label class="form-label">Category</label>'))

    class Meta:
        model = Product
        fields = ["name", "image", "price", "vat", "category", "enabled"]
