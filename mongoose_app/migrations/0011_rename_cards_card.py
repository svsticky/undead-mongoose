# Generated by Django 3.2.9 on 2021-11-22 20:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0010_remove_topuptransaction_refunded'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Cards',
            new_name='Card',
        ),
    ]