"""
Exceptions for the documents app.

Raised by the generation service when generation cannot proceed or fails.
Views catch these and display the message to the user.
"""


class DocumentGenerationError(Exception):
    """Raised when document generation fails or preconditions are not met."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)
