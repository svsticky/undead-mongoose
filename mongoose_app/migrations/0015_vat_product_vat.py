# Generated by Django 4.0 on 2021-12-20 12:25

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0014_remove_user_age_user_birthday'),
    ]

    operations = [
        migrations.CreateModel(
            name='VAT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.IntegerField(validators=[django.core.validators.MinValueValidator(limit_value=0, message="Percentage can't be lower than 0"), django.core.validators.MaxValueValidator(limit_value=100, message="Percentage can't be higher than 100")])),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='vat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mongoose_app.vat', verbose_name='BTW'),
        ),
    ]