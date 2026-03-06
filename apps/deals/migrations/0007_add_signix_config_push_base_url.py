from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deals", "0006_add_signature_transaction_sync_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="signixconfig",
            name="push_base_url",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
    ]
