# Generated by Django 3.2.9 on 2021-11-22 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0009_category_alcoholic'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topuptransaction',
            name='refunded',
        ),
    ]
