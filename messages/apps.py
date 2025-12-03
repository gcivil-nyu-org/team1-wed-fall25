from django.apps import AppConfig


class MessagesConfig(AppConfig):
    """Configuration for the messages app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "messages"
    label = "user_messages"  # Avoid conflict with django.contrib.messages
    verbose_name = "User Messages"

    def ready(self):
        # Import signals when app is ready
        pass

