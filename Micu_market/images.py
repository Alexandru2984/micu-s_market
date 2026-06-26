import logging
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image as PilImage

logger = logging.getLogger(__name__)


def optimize_image_field(image_field, max_size, quality=85):
    """Resize an ImageField through its storage backend, not the local path API."""
    if not image_field or not image_field.name:
        return None

    storage = image_field.storage
    name = image_field.name

    try:
        with storage.open(name, "rb") as source:
            image = PilImage.open(source)
            image.load()

            if getattr(image, "is_animated", False):
                return name

            if image.width <= max_size[0] and image.height <= max_size[1]:
                return name

            output_format = _normalise_output_format(image.format)
            image.thumbnail(max_size, PilImage.Resampling.LANCZOS)
            image = _prepare_image_for_format(image, output_format)

            output = BytesIO()
            save_options = {"optimize": True}
            if output_format in {"JPEG", "WEBP"}:
                save_options["quality"] = quality
            image.save(output, format=output_format, **save_options)

        storage.delete(name)
        return storage.save(name, ContentFile(output.getvalue()))
    except Exception:
        logger.exception("image_optimization_failed", extra={"image_name": name})
        return name


def _normalise_output_format(image_format):
    image_format = (image_format or "JPEG").upper()
    if image_format == "JPG":
        return "JPEG"
    if image_format in {"JPEG", "PNG", "WEBP"}:
        return image_format
    return "JPEG"


def _prepare_image_for_format(image, output_format):
    if output_format != "JPEG":
        return image

    if image.mode in {"RGB", "L"}:
        return image

    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = PilImage.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    return image.convert("RGB")
