"""Image intake for the camera path.

Phone cameras produce large, rotated, occasionally corrupt files. This
module normalizes them in memory only - nothing is written to disk, which
is part of the zero-retention guarantee.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

# Beyond this the request is rejected rather than silently downscaled to the
# point where digits stop being legible.
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
# Longest edge fed to OCR. Large enough for small print on a lab report,
# small enough to keep GPU latency predictable.
MAX_EDGE_PX = 2400
# Below this an image cannot hold readable report text.
MIN_EDGE_PX = 320


class UnreadableImageError(ValueError):
    """The bytes are not a decodable image."""


class ImageTooLargeError(ValueError):
    """The upload exceeds the configured size limit."""


class ImageTooSmallError(ValueError):
    """The image is too small to contain readable report text."""


def prepare_image(data: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Decode, orient, downscale, and re-encode an uploaded photo.

    Returns PNG bytes ready for OCR. Raises rather than guessing when the
    input is unusable.
    """
    if not data:
        raise UnreadableImageError("No image data was received.")
    if len(data) > max_bytes:
        raise ImageTooLargeError(
            f"The image is larger than the {max_bytes // (1024 * 1024)} MB limit."
        )

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise UnreadableImageError(
            "This file could not be read as an image."
        ) from exc

    # Honour the EXIF orientation phones set instead of rotating pixels.
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    if max(image.size) < MIN_EDGE_PX:
        raise ImageTooSmallError(
            "This image is too small to read. Move closer and retake the photo."
        )

    if max(image.size) > MAX_EDGE_PX:
        scale = MAX_EDGE_PX / max(image.size)
        new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        image = image.resize(new_size, Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
