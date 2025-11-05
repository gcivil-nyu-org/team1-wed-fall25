# Generated migration file
# Save as: loc_detail/migrations/0011_comment_images_and_reports.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("loc_detail", "0010_alter_publicart_thumbnail"),
    ]

    operations = [
        # Remove old single image field from ArtComment
        migrations.RemoveField(
            model_name="artcomment",
            name="image",
        ),
        # Create CommentImage model for multiple images
        migrations.CreateModel(
            name="CommentImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        help_text="Review photo", upload_to="review_images/"
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "comment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="loc_detail.artcomment",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "uploaded_at"],
            },
        ),
        # Create CommentReport model
        migrations.CreateModel(
            name="CommentReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "reasons",
                    models.JSONField(help_text="List of selected report reasons"),
                ),
                (
                    "additional_info",
                    models.TextField(
                        blank=True, help_text="Additional details about the report"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("reviewing", "Under Review"),
                            ("resolved", "Resolved"),
                            ("dismissed", "Dismissed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("admin_notes", models.TextField(blank=True)),
                (
                    "comment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to="loc_detail.artcomment",
                    ),
                ),
                (
                    "reporter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comment_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("comment", "reporter")},
            },
        ),
    ]
