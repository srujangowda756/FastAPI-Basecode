import io

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from core.config import settings

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PIXELS = 25_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


async def read_limited(file: UploadFile) -> bytes:
    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file too large")
    return data


def _encode(img: Image.Image, size: int) -> bytes:
    copy = img.copy()
    copy.thumbnail((size, size))
    buf = io.BytesIO()
    # no exif/metadata is passed, so GPS data is dropped
    copy.save(buf, format="WEBP", quality=85)
    return buf.getvalue()


def _process(raw: bytes) -> tuple[bytes, bytes]:
    try:
        img = Image.open(io.BytesIO(raw))
        if img.format not in ALLOWED_FORMATS:
            raise ValueError("unsupported type")
        if img.width * img.height > MAX_PIXELS:
            raise ValueError("image too large")
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("invalid image")
    return _encode(img, 1024), _encode(img, 256)


async def process_image(raw: bytes) -> tuple[bytes, bytes]:
    try:
        return await run_in_threadpool(_process, raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid or unsupported image")
