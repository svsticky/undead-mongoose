# Generated by Django 4.0 on 2021-12-09 20:41

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0013_alter_saletransaction_user_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='age',
        ),
        migrations.AddField(
            model_name='user',
            name='birthday',
            field=models.DateField(default=datetime.datetime(2021, 12, 9, 20, 41, 33, 303697, tzinfo=utc)),
            preserve_default=False,
        ),
    ]