from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

# adjust if the app is different
from listings.models import Listing, ListingImage


def get_font(size=72):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def img_field_is_valid(img_field):
    try:
        name = getattr(img_field, "name", "")
        if not name:
            return False
        if not default_storage.exists(name):
            return False
        size = getattr(img_field, "size", None)
        return True if size is None else (size > 0)
    except Exception:
        return False


def listing_has_valid_image(listing):
    # look for images in the usual relations
    for attr in ("images", "photos", "pictures", "listingimage_set", "image_set"):
        if hasattr(listing, attr):
            for im in getattr(listing, attr).all():
                if img_field_is_valid(getattr(im, "image", None)):
                    return True
    # fall back to a single field on Listing (if it exists)
    for field in ("image", "cover_image", "primary_image"):
        if hasattr(listing, field) and img_field_is_valid(getattr(listing, field)):
            return True
    return False


def make_img_bytes(title, subtitle=""):
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (230, 232, 236))
    d = ImageDraw.Draw(img)

    # large centered title, scaled to fit
    f = get_font(96)
    while d.textlength(title, font=f) > W - 160 and getattr(f, "size", 96) > 36:
        f = get_font(getattr(f, "size", 96) - 6)
    tw = d.textlength(title, font=f)
    try:
        th = f.getbbox(title)[3] - f.getbbox(title)[1]
    except Exception:
        th = 100
    x = (W - tw) // 2
    y = H // 2 - th
    d.text((x, y), title, font=f, fill=(30, 30, 30))

    if subtitle:
        f2 = get_font(max(36, int(getattr(f, "size", 96) * 0.5)))
        tw2 = d.textlength(subtitle, font=f2)
        d.text(((W - tw2) // 2, y + th + 20), subtitle, font=f2, fill=(90, 90, 90))

    # small watermark
    f3 = get_font(24)
    d.text((W - 240, H - 40), "Micu’s Market", font=f3, fill=(120, 124, 130))

    buf = BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def get_images_manager(listing):
    for attr in ("images", "photos", "pictures", "listingimage_set", "image_set"):
        if hasattr(listing, attr):
            return getattr(listing, attr)
    return None


def mark_primary_on_image(listing, new_img_obj):
    """
    If the image model has an is_primary / is_main boolean field and there is
    NOT already a marked photo, mark the placeholder. Does NOT touch Listing.main_image (property).
    """
    rel = get_images_manager(listing)
    if rel is None:
        return
    for f in ("is_primary", "is_main"):
        if hasattr(new_img_obj, f):
            try:
                if not rel.filter(**{f: True}).exists():
                    setattr(new_img_obj, f, True)
                    new_img_obj.save(update_fields=[f])
            except Exception:
                pass
            break


def run():
    created = 0
    skipped = 0
    failed = 0

    qs = Listing.objects.all().select_related("category").prefetch_related("images")
    for lst in qs:
        try:
            if listing_has_valid_image(lst):
                skipped += 1
                continue

            title = (lst.title or "Listing")[:48]
            cat = getattr(getattr(lst, "category", None), "name", "") or ""
            subtitle = f"#{cat}" if cat else ""

            data = make_img_bytes(title, subtitle)
            filename = f"{slugify(title) or 'listing'}_{lst.pk}_placeholder.jpg"

            obj = ListingImage(listing=lst)
            obj.image.save(filename, ContentFile(data), save=True)

            # Count it as created even if we cannot set any "primary" marker
            created += 1

            # Best-effort: if the model has a primary flag, set it
            try:
                mark_primary_on_image(lst, obj)
            except Exception:
                pass

            if created <= 3:
                try:
                    print("CREATED", lst.pk, obj.image.url)
                except Exception:
                    pass

        except Exception as e:
            failed += 1
            print("ERROR", lst.pk, str(e))

    print("SUMMARY created", created, "skipped", skipped, "failed", failed)


if __name__ == "__main__":
    run()
