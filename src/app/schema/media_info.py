import base64
import contextlib
from copy import deepcopy
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel, Field, root_validator, validator

from app.database import db_instance
from app.exceptions import BadRequest
from app.type import FileType


class BaseMediaInfo(BaseModel):
    @property
    def db_value(self) -> Dict:
        obj = self.dict(exclude_unset=True, exclude_none=True)
        if raw_file := obj.get("raw_file"):
            obj["raw_file"] = raw_file.getvalue()
        if processed_files := obj.get("processed_files"):
            obj["processed_files"] = [
                processed_file.getvalue() for processed_file in processed_files
            ]
        return obj


class CreateMediaInfo(BaseMediaInfo):
    raw_file: BytesIO
    file_type: FileType
    file_name: str
    processed_files: Optional[List[BytesIO]]

    class Config:
        arbitrary_types_allowed = True

    @root_validator
    def validate_file(cls, values):
        def _get_file_type(file_bytes):
            file_bytes_copy = deepcopy(file_bytes)
            try:
                convert_from_bytes(file_bytes_copy.getvalue())
                return FileType.PDF
            except Exception:
                ...

            supported_img_formats = {
                FileType.PNG: lambda: Image.open(file_bytes).verify(),
                FileType.JPG: lambda: Image.open(file_bytes).verify(),
                FileType.JPEG: lambda: Image.open(file_bytes).verify(),
            }
            for format, conversion_function in supported_img_formats.items():
                with contextlib.suppress(IOError, SyntaxError):
                    conversion_function()
                    return format
            raise BadRequest(message="Unsupported/Invalid file format")

        if values.get("raw_file", None) is None:
            return values
        actual_file_type = _get_file_type(values.get("raw_file"))
        if values.get("file_type") != actual_file_type:
            BadRequest(
                message=f'Invalid file type, expected:{values.get("file_type")}, got:{actual_file_type}'
            )
        return values


class EditMediaInfo(BaseMediaInfo):
    file_name: Optional[str]
    processed_files: Optional[List[BytesIO]]

    class Config:
        arbitrary_types_allowed = True


class MediaInfoResponse(BaseModel, orm_mode=True):
    id: str
    file_name: str
    file_type: FileType


class PartialMediaInfoResponse(MediaInfoResponse, orm_mode=True):
    idx: List[int] = [-1]
    raw_file: Optional[bytes]
    processed_files: Optional[List[bytes]]
    processed_total_count: Optional[int] = 1
    processed_count: Optional[int] = 0

    @classmethod
    def response_value(
        cls, obj, source: Literal["all", "processed", "raw"], idx: List[int] = None
    ) -> Dict:
        def _decode_raw_bytes(value):
            if isinstance(value, bytes):
                return base64.b64encode(obj.raw_file).decode("utf-8")
            return [base64.b64encode(file).decode("utf-8") for file in value]

        idx = idx or [-1]
        processed_file_count = len(obj.processed_files) if obj.processed_files else 0
        response = {
            "id": obj.id,
            "idx": idx,
            "file_name": obj.file_name,
            "file_type": obj.file_type,
            "processed_total_count": processed_file_count,
        }
        if source in ["all", "raw"] and obj.raw_file:
            response["raw_file"] = _decode_raw_bytes(obj.raw_file)
        if source in ["all", "processed"] and obj.processed_files:
            if any(i >= processed_file_count or i < -1 for i in idx):
                raise BadRequest("Invalid indexes selected")
            processed_files = (
                [obj.processed_files[i] for i in idx]
                if idx[0] != -1
                else obj.processed_files
            )
            response.update(
                {
                    "processed_files": _decode_raw_bytes(processed_files),
                    "processed_count": len(processed_files),
                }
            )
        return response


class MessageResponse(BaseModel):
    detail: str


if __name__ == "__main__":
    from app.database import db_instance
    from app.models.main import MediaInfo

    mi = MediaInfo.filter()
    mi = mi[0]
    session = db_instance.initialize_session()
    from pprint import pprint

    pprint(MediaInfoResponse.from_orm(mi).dict())
    session.close()
