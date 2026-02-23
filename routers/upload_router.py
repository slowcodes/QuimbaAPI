from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from dtos.auth import UserDTO
from security.dependencies import get_current_active_user

upload_router = APIRouter(prefix="/uploads/img/config", tags=["Uploads"])


@upload_router.post("/", status_code=status.HTTP_201_CREATED)
def upload_config_image(
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file name provided")

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads are allowed")

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix
    stored_name = f"{uuid4().hex}{extension}"

    upload_dir = Path("uploads") / "img" / "config"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / stored_name

    try:
        with output_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    finally:
        file.file.close()

    return {
        "message": "Upload successful",
        "original_filename": original_name,
        "stored_filename": stored_name,
        "content_type": file.content_type,
        "size": output_path.stat().st_size,
        "path": f"/uploads/img/config/{stored_name}",
    }
