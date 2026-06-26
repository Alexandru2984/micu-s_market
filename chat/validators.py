import zipfile

from PIL import Image as PilImage


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 5
MAX_OFFICE_ARCHIVE_FILES = 1000
MAX_OFFICE_UNCOMPRESSED_SIZE = 50 * 1024 * 1024
MAX_OFFICE_MEMBER_SIZE = 20 * 1024 * 1024

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "xls", "xlsx"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

ALLOWED_CONTENT_TYPES = {
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "gif": {"image/gif"},
    "webp": {"image/webp"},
    "pdf": {"application/pdf"},
    "txt": {"text/plain"},
    "doc": {"application/msword", "application/octet-stream"},
    "xls": {"application/vnd.ms-excel", "application/octet-stream"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    },
}

OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def get_extension(uploaded_file):
    name = uploaded_file.name or ""
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def is_allowed_chat_attachment(uploaded_file):
    ext = get_extension(uploaded_file)
    if ext not in ALLOWED_EXTENSIONS:
        return False

    if uploaded_file.size > MAX_ATTACHMENT_SIZE:
        return False

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES[ext]:
        return False

    if ext in IMAGE_EXTENSIONS:
        return _is_valid_image(uploaded_file)

    if ext == "pdf":
        return _starts_with(uploaded_file, b"%PDF-")

    if ext == "txt":
        return _is_plain_text(uploaded_file)

    if ext in {"doc", "xls"}:
        return _starts_with(uploaded_file, OLE_SIGNATURE)

    if ext in {"docx", "xlsx"}:
        return _is_valid_office_zip(uploaded_file, ext)

    return False


def _is_valid_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        image = PilImage.open(uploaded_file)
        image.verify()
        return True
    except Exception:
        return False
    finally:
        uploaded_file.seek(0)


def _starts_with(uploaded_file, signature):
    try:
        uploaded_file.seek(0)
        return uploaded_file.read(len(signature)) == signature
    finally:
        uploaded_file.seek(0)


def _is_plain_text(uploaded_file):
    try:
        uploaded_file.seek(0)
        sample = uploaded_file.read(4096)
        if b"\x00" in sample:
            return False
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
    finally:
        uploaded_file.seek(0)


def _is_valid_office_zip(uploaded_file, ext):
    try:
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_OFFICE_ARCHIVE_FILES:
                return False
            if sum(info.file_size for info in infos) > MAX_OFFICE_UNCOMPRESSED_SIZE:
                return False
            if any(info.file_size > MAX_OFFICE_MEMBER_SIZE for info in infos):
                return False

            names = {info.filename for info in infos}
            if any(_is_unsafe_zip_name(name) for name in names):
                return False
            if "[Content_Types].xml" not in names:
                return False
            prefix = "word/" if ext == "docx" else "xl/"
            return any(name.startswith(prefix) for name in names)
    except zipfile.BadZipFile:
        return False
    finally:
        uploaded_file.seek(0)


def _is_unsafe_zip_name(name):
    return name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/")
