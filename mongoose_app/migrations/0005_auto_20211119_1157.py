# Generated by Django 3.2.9 on 2021-11-19 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0004_auto_20211118_1410'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saletransaction',
            name='transaction_sum',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='topuptransaction',
            name='transaction_sum',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
    ]
