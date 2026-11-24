import django.contrib.postgres.fields
from django.db import migrations, models


def copy_barcode(apps, schema_editor):
    Product = apps.get_model("mongoose_app", "Product")
    for product in Product.objects.exclude(barcode__isnull=True).exclude(barcode=""):
        product.barcodes = [product.barcode]
        product.save(update_fields=["barcodes"])


def copy_barcodes_back(apps, schema_editor):
    Product = apps.get_model("mongoose_app", "Product")
    for product in Product.objects.exclude(barcodes=[]):
        product.barcode = product.barcodes[0]
        product.save(update_fields=["barcode"])


class Migration(migrations.Migration):

    dependencies = [
        ("mongoose_app", "0037_product_barcode"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="barcodes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=80), blank=True, default=list, size=10
            ),
        ),
        migrations.RunPython(copy_barcode, copy_barcodes_back),
        migrations.RemoveField(
            model_name="product",
            name="barcode",
        ),
    ]
