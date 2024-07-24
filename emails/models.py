from django.db import models

class Email(models.Model):
    sender = models.EmailField()
    subject = models.CharField(max_length=255)
    body_text = models.TextField(null=True, blank=True)
    body_html = models.TextField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)  # Make this nullable too
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Make this nullable

    def __str__(self):
        return f"{self.subject} from {self.sender}"

    class Meta:
        ordering = ['-received_at']