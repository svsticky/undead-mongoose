# Generated by Django 4.0 on 2022-01-17 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0019_alter_user_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_id',
            field=models.IntegerField(unique=True),
        ),
    ]
