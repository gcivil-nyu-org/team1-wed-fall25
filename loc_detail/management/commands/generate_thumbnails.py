from django.core.management.base import BaseCommand
from django.db import models
from loc_detail.models import PublicArt


class Command(BaseCommand):
    help = "Generate thumbnails for existing PublicArt images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Regenerate thumbnails even if present"
        )

    def handle(self, *args, **options):
        qs = PublicArt.objects.filter(image__isnull=False)
        if not options["force"]:
            qs = qs.filter(models.Q(thumbnail__isnull=True) | models.Q(thumbnail=""))

        total = qs.count()
        self.stdout.write(f"Processing {total} items...")
        for art in qs.iterator():
            try:
                art.image.open()
                thumb = art.make_thumbnail(art.image)
                if thumb:
                    art.thumbnail.save(thumb.name, thumb, save=False)
                    art.save()
                    self.stdout.write(f"OK: {art.pk}")
                else:
                    self.stdout.write(f"SKIP (make_thumbnail returned None): {art.pk}")
            except Exception as e:
                self.stdout.write(f"ERROR {art.pk}: {e}")
        self.stdout.write("Done.")
