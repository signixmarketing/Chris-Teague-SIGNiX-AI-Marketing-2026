import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deals", "0007_add_signix_config_push_base_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="SignatureTransactionEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=50)),
                ("occurred_at", models.DateTimeField()),
                ("refid", models.CharField(blank=True, max_length=100)),
                ("pid", models.CharField(blank=True, max_length=100)),
                (
                    "signature_transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="deals.signaturetransaction",
                    ),
                ),
            ],
            options={
                "verbose_name": "Signature transaction event",
                "verbose_name_plural": "Signature transaction events",
                "ordering": ["occurred_at"],
            },
        ),
    ]
