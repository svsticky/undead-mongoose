from django.apps import AppConfig
from constance.apps import ConstanceConfig

class MongooseAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mongoose_app'
    verbose_name = "Undead Mongoose"

class CustomConstance(ConstanceConfig):
    verbose_name = "Global Settings"