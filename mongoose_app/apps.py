from django.apps import AppConfig


class MongooseAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mongoose_app'
    verbose_name = "Undead Mongoose"
