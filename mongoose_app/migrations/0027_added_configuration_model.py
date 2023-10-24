# Generated by Django 4.0.2 on 2023-10-12 14:48

from django.db import migrations, models


class Migration(migrations.Migration):
    def create_initial_row(self):
        Configuration = self.get_model('mongoose_app', 'Configuration')
        Configuration.objects.create(alc_time="17:00:00")

    dependencies = [
        ('mongoose_app', '0026_type_for_top_up_transactions_and_image_not_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alc_time', models.TimeField(default='17:00:00', help_text='Time from which alcohol sales are allowed')),
            ],
        ),
        migrations.RunPython(create_initial_row)
    ]
