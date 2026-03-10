"""
Signal handlers for the deals app.

When a SignatureTransaction is deleted (including via Delete Transaction History
or cascade from DocumentSet), the stored audit trail and certificate of completion
files are removed from media storage so no orphaned files remain.
"""

import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.deals.models import SignatureTransaction

logger = logging.getLogger(__name__)


def _delete_file_from_storage(file_field):
    """Delete the file from storage if the field is set. Log and continue on error."""
    if not file_field:
        return
    try:
        file_field.delete(save=False)
    except OSError as e:
        logger.warning("Could not delete transaction file %s: %s", file_field.name, e)


@receiver(pre_delete, sender=SignatureTransaction)
def delete_signature_transaction_files(sender, instance, **kwargs):
    """
    Before a SignatureTransaction is deleted, remove its audit trail and
    certificate of completion files from media storage.
    """
    _delete_file_from_storage(instance.audit_trail_file)
    _delete_file_from_storage(instance.certificate_of_completion_file)
