from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=30)

class Product(models.Model):
    name = models.CharField(max_length=30)
    price = models.FloatField()
    image = models.ImageField()
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
    )

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

class User(models.Model):
    user_id = models.CharField(max_length=30)
    balance = product_price = models.FloatField()

class Cards(models.Model):
    card_id = models.CharField(max_length=8)
    active = models.BooleanField()
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
