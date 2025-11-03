from django.core.management.base import BaseCommand
from django.db import transaction

from loc_detail.models import PublicArt


class Command(BaseCommand):
    help = "Downsample PublicArt images exceeding MAX_IMAGE_SIZE."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-downsample",
            action="store_true",
            help="Attempt to downsample all images regardless of current size.",
        )
        parser.add_argument(
            "--regenerate-thumbnails",
            action="store_true",
            help="Regen thumbs for images (all images with --force-downsample).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't write changes; just report which images would be changed.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit number of images processed (useful for testing).",
        )

    def handle(self, *args, **options):
        qs = PublicArt.objects.filter(image__isnull=False).exclude(image="")
        if options.get("limit"):
            qs = qs[: options["limit"]]

        total = qs.count()
        self.stdout.write(f"Found {total} PublicArt records with images to inspect.")

        processed = 0
        errors = 0

        for art in qs.iterator():
            processed += 1
            self.stdout.write(
                f"[{processed}/{total}] id={art.pk} image={art.image.name}"
            )

            try:
                # Ensure file is open/readable by storage backends
                try:
                    art.image.open()
                except Exception:
                    # some storages auto-open; let downsample_image handle
                    pass

                downsampled = None
                if not options["dry_run"]:
                    # Return ContentFile when downsampling is needed
                    downsampled = art.downsample_image(art.image)
                else:
                    # In dry-run, call but do not save
                    try:
                        downsampled = art.downsample_image(art.image)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  dry-run error calling downsample_image: {e}"
                            )
                        )
                        downsampled = None

                if downsampled:
                    self.stdout.write(
                        self.style.SUCCESS("  Downsample candidate produced by model.")
                    )
                    if not options["dry_run"]:
                        old_name = art.image.name
                        # save downsampled image (save=False to avoid recursion)
                        art.image.save(downsampled.name, downsampled, save=False)
                        # remove old file if different
                        try:
                            if (
                                old_name
                                and old_name != art.image.name
                                and art.image.storage.exists(old_name)
                            ):
                                art.image.storage.delete(old_name)
                        except Exception:
                            # non-fatal
                            pass
                        self.stdout.write(
                            f"  Saved downsampled image as: {art.image.name}"
                        )
                else:
                    self.stdout.write("  No downsample needed/produced.")

                # regenerate thumbnail if requested or if thumbnail missing
                regenerate = options["regenerate_thumbnails"]
                if not regenerate:
                    # regenerate if no thumbnail present
                    if not art.thumbnail or art.thumbnail == "":
                        regenerate = True

                if regenerate:
                    if options["dry_run"]:
                        self.stdout.write("  (dry-run) would regenerate thumbnail")
                    else:
                        thumb_cf = art.make_thumbnail(art.image)
                        if thumb_cf:
                            # remove old thumbnail if exists (guard)
                            try:
                                old_thumb = None
                                if art.pk:
                                    old = PublicArt.objects.get(pk=art.pk)
                                    old_thumb = getattr(old, "thumbnail", None)
                                    if (
                                        old_thumb
                                        and old_thumb.name
                                        and old_thumb.storage.exists(old_thumb.name)
                                    ):
                                        old_thumb.storage.delete(old_thumb.name)
                            except Exception:
                                pass
                            art.thumbnail.save(thumb_cf.name, thumb_cf, save=False)
                            self.stdout.write(
                                f"  Thumbnail saved: {art.thumbnail.name}"
                            )
                        else:
                            self.stdout.write("  Thumbnail generation returned None.")

                # finally persist changes
                if not options["dry_run"]:
                    # wrap in transaction per-object for safety
                    try:
                        with transaction.atomic():
                            art.save()
                    except Exception as e:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(f"  Error saving object id={art.pk}: {e}")
                        )
                        continue

                self.stdout.write(self.style.SUCCESS(f"  Processed id={art.pk}"))
            except Exception as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"  Unexpected error for id={art.pk}: {exc}")
                )

        self.stdout.write("Done.")
        self.stdout.write(f"Processed: {processed}, Errors: {errors}")
