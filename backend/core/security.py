from fastapi import HTTPException, UploadFile, status
from loguru import logger

# Try importing magic for robust content sniffing, fallback to stdlib MIME detection if absent
try:
    import magic
except ImportError:
    magic = None

# Security Configuration limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/json",
    "text/markdown",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
}


def validate_upload_file(file: UploadFile) -> None:
    """
    Validates uploaded file size limits and MIME content types to secure the system boundary.
    Uses fallback mechanisms if python-magic is not installed.
    """
    # 1. Size Validation
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer

    if file_size > MAX_UPLOAD_SIZE:
        logger.warning(
            f"Security reject: uploaded file size ({file_size} bytes) exceeds limit ({MAX_UPLOAD_SIZE} bytes)."
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {MAX_UPLOAD_SIZE / (1024 * 1024)} MB.",
        )

    # 2. MIME Content Type Validation
    content_type = file.content_type

    # Try using python-magic if available for deep byte analysis
    if magic and hasattr(magic, "from_buffer"):
        try:
            # Read first 2048 bytes for signature analysis
            header_bytes = file.file.read(2048)
            file.file.seek(0)  # Reset pointer
            content_type = magic.from_buffer(header_bytes, mime=True)
        except Exception as me:
            logger.warning(
                f"python-magic validation failed: {me}. Falling back to default headers."
            )

    if content_type not in ALLOWED_MIME_TYPES:
        # Check by extension fallback if MIME header is generic
        ext = file.filename.split(".")[-1].lower() if file.filename else ""
        ext_to_mime = {
            "pdf": "application/pdf",
            "json": "application/json",
            "md": "text/markdown",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        fallback_mime = ext_to_mime.get(ext)
        if fallback_mime not in ALLOWED_MIME_TYPES:
            logger.warning(
                f"Security reject: file '{file.filename}' has unsupported MIME/type '{content_type}' / extension '{ext}'."
            )
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file format. Allowed formats: PDF, JSON, Markdown, DOCX, PPTX, TXT.",
            )

    logger.info(
        f"File upload validated: '{file.filename}' ({file_size} bytes, MIME: {content_type})."
    )
