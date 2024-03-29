# Generated by Django 4.0.2 on 2023-12-12 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mongoose_app', '0027_added_configuration_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='topuptransaction',
            name='type',
            field=models.IntegerField(choices=[(1, 'Pin'), (2, 'Credit card'), (3, 'Mollie')], default=1),
        ),
    ]
