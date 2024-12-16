# Generated by Django 4.0 on 2024-12-16 16:18

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0028_save_email_in_user_add_mollie'),
    ]

    operations = [
        migrations.CreateModel(
            name='IDealTransaction',
            fields=[
                ('transaction_sum', models.DecimalField(decimal_places=2, max_digits=6)),
                ('date', models.DateField(auto_now=True)),
                ('transaction_id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('status', models.IntegerField(choices=[(1, 'PAID'), (2, 'PENDING'), (3, 'OPEN'), (4, 'CANCELLED')], default=3)),
                ('added', models.BooleanField(default=False)),
                ('user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mongoose_app.user')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
