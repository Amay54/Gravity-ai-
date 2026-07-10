import io

import pytest
from fastapi import HTTPException, UploadFile

from backend.core.security import validate_upload_file


def test_valid_file_validation() -> None:
    # Creating a valid mock in-memory PDF file
    file_bytes = b"%PDF-1.4 Mock PDF Content"
    mock_file = io.BytesIO(file_bytes)
    upload_file = UploadFile(
        filename="test.pdf", file=mock_file, headers={"content-type": "application/pdf"}
    )

    # Should not raise exception
    validate_upload_file(upload_file)


def test_invalid_mime_validation() -> None:
    file_bytes = b"<html>Body</html>"
    mock_file = io.BytesIO(file_bytes)
    upload_file = UploadFile(
        filename="test.html", file=mock_file, headers={"content-type": "text/html"}
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_upload_file(upload_file)
    assert exc_info.value.status_code == 415


def test_oversized_file_validation() -> None:
    # 11MB file bytes
    file_bytes = b"0" * (11 * 1024 * 1024)
    mock_file = io.BytesIO(file_bytes)
    upload_file = UploadFile(
        filename="large.pdf", file=mock_file, headers={"content-type": "application/pdf"}
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_upload_file(upload_file)
    assert exc_info.value.status_code == 413
