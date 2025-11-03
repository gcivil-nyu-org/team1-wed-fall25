import os
import shutil
import tempfile
from io import BytesIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from PIL import Image

from loc_detail.models import PublicArt


def create_test_image(filename="test.jpg", size=(800, 600), color=(255, 0, 0)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "JPEG")
    buf.seek(0)
    return SimpleUploadedFile(filename, buf.read(), content_type="image/jpeg")


class ThumbnailTests(TestCase):
    def setUp(self):
        self._tmp_media = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp_media, ignore_errors=True)

    def test_thumbnail_created_on_save(self):
        with self.settings(MEDIA_ROOT=self._tmp_media):
            img = create_test_image("orig.jpg", (800, 600))
            art = PublicArt.objects.create(title="T1", image=img)
            art.refresh_from_db()

            self.assertTrue(
                bool(art.thumbnail), "Expected thumbnail to be set after save"
            )

            thumb_path = os.path.join(settings.MEDIA_ROOT, art.thumbnail.name)
            self.assertTrue(
                os.path.exists(thumb_path), f"Thumbnail file missing: {thumb_path}"
            )

            im = Image.open(thumb_path)
            self.assertEqual(im.format, "JPEG")
            self.assertLessEqual(im.width, PublicArt.THUMBNAIL_SIZE[0])
            self.assertLessEqual(im.height, PublicArt.THUMBNAIL_SIZE[1])

    def test_thumbnail_regenerated_on_replace(self):
        with self.settings(MEDIA_ROOT=self._tmp_media):
            img1 = create_test_image("a.jpg", (800, 600))
            art = PublicArt.objects.create(title="T2", image=img1)
            old_thumb = art.thumbnail.name
            old_thumb_path = os.path.join(settings.MEDIA_ROOT, old_thumb)
            self.assertTrue(os.path.exists(old_thumb_path))

            img2 = create_test_image("b.jpg", (200, 200))
            art.image = img2
            art.save()
            art.refresh_from_db()

            self.assertTrue(bool(art.thumbnail))
            self.assertNotEqual(art.thumbnail.name, old_thumb)
            self.assertFalse(
                os.path.exists(old_thumb_path), "Old thumbnail should have been deleted"
            )

    def test_thumbnail_deleted_when_image_removed(self):
        with self.settings(MEDIA_ROOT=self._tmp_media):
            img = create_test_image("to_delete.jpg")
            art = PublicArt.objects.create(title="T3", image=img)
            thumb_name = art.thumbnail.name
            thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_name)
            self.assertTrue(os.path.exists(thumb_path))

            art.image = None
            art.save()
            art.refresh_from_db()

            self.assertFalse(bool(art.thumbnail))
            self.assertFalse(
                os.path.exists(thumb_path),
                "Thumbnail file should be deleted when image removed",
            )

    def test_make_thumbnail_accepts_filelike_and_returns_contentfile(self):
        with self.settings(MEDIA_ROOT=self._tmp_media):
            f = BytesIO()
            Image.new("RGB", (400, 400), (10, 20, 30)).save(f, "JPEG")
            f.seek(0)
            upload = SimpleUploadedFile(
                "inmem.jpg", f.read(), content_type="image/jpeg"
            )

            thumb_cf = PublicArt().make_thumbnail(upload)
            self.assertIsNotNone(
                thumb_cf, "make_thumbnail returned None for valid input"
            )
            self.assertTrue(thumb_cf.name.startswith("thumb_"))
            img_bytes = BytesIO(thumb_cf.read())
            im = Image.open(img_bytes)
            self.assertEqual(im.format, "JPEG")
            self.assertLessEqual(im.width, PublicArt.THUMBNAIL_SIZE[0])
            self.assertLessEqual(im.height, PublicArt.THUMBNAIL_SIZE[1])

    def test_downsample_large_image_on_save(self):
        with self.settings(MEDIA_ROOT=self._tmp_media):
            large = create_test_image("large.jpg", size=(4000, 3000))
            art = PublicArt.objects.create(title="T4", image=large)
            art.refresh_from_db()

            # saved original should be downsampled to within MAX_IMAGE_SIZE
            saved_image_path = os.path.join(settings.MEDIA_ROOT, art.image.name)
            self.assertTrue(os.path.exists(saved_image_path))
            im = Image.open(saved_image_path)
            self.assertLessEqual(im.width, PublicArt.MAX_IMAGE_SIZE[0])
            self.assertLessEqual(im.height, PublicArt.MAX_IMAGE_SIZE[1])
