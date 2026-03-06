from django.db import migrations, models


def backfill_signature_transaction_sync_fields(apps, schema_editor):
    SignatureTransaction = apps.get_model("deals", "SignatureTransaction")

    for transaction in SignatureTransaction.objects.filter(signer_count__isnull=True):
        transaction.status = "Complete"
        transaction.signer_count = 2
        transaction.signers_completed_count = 2
        transaction.signers_completed_refids = []
        if transaction.completed_at is None:
            transaction.completed_at = transaction.submitted_at
        transaction.status_last_updated = transaction.submitted_at
        transaction.save(
            update_fields=[
                "status",
                "signer_count",
                "signers_completed_count",
                "signers_completed_refids",
                "completed_at",
                "status_last_updated",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("deals", "0005_add_signer_order_and_authentication"),
    ]

    operations = [
        migrations.AddField(
            model_name="signaturetransaction",
            name="audit_trail_file",
            field=models.FileField(blank=True, upload_to="signature_transactions/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="signaturetransaction",
            name="certificate_of_completion_file",
            field=models.FileField(blank=True, upload_to="signature_transactions/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="signaturetransaction",
            name="signer_count",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="signaturetransaction",
            name="signers_completed_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="signaturetransaction",
            name="signers_completed_refids",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="signaturetransaction",
            name="status_last_updated",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="signaturetransaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("Submitted", "Submitted"),
                    ("In Progress", "In Progress"),
                    ("Suspended", "Suspended"),
                    ("Complete", "Complete"),
                    ("Cancelled", "Cancelled"),
                    ("Expired", "Expired"),
                ],
                default="Submitted",
                max_length=50,
            ),
        ),
        migrations.RunPython(
            backfill_signature_transaction_sync_fields,
            migrations.RunPython.noop,
        ),
    ]
