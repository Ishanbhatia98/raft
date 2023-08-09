import contextlib
import logging
import os
import uuid
from copy import deepcopy
from io import BytesIO
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import PyPDF2
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel, root_validator

from app.database import db_instance, get_db_session
from app.models.main import MediaInfo
from app.schema.media_info import (
    CreateMediaInfo,
    MediaInfoResponse,
    MessageResponse,
    PartialMediaInfoResponse,
)
from app.type import FileType
from app.utils import convert_img_to_png_io, convert_pdf_to_png_io, db_session_wrapper
from app.workers.tasks import process_raw_file

router = APIRouter(tags=["CONVERTER"])


@db_session_wrapper
@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=List[MediaInfoResponse],
)
async def upload_files(file_type: FileType, file: UploadFile):
    """
    Upload and process files.

    Args:
        file_type (FileType): The type of the uploaded file.
        file (UploadFile): The file to be uploaded.

    Returns:
        List[MediaInfoResponse]: List of created media information.

    Raises:
        HTTPError: If an error occurs during processing
    """
    media_infos = [
        MediaInfo.create(
            CreateMediaInfo(
                file_type=file_type,
                raw_file=BytesIO(file.file.read()),
                file_name=file.filename,
            )
        )
    ]
    for media_info in media_infos:
        process_raw_file.apply_async(args=[media_info.id])
    return media_infos


@db_session_wrapper
@router.get(
    "/download/{type}/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=Union[PartialMediaInfoResponse, MessageResponse],
)
async def fetch_processed_file(
    source: Literal["raw", "processed", "all"], media_id: str, idx: str = "-1"
):
    """
    Fetch processed file information.

    Args:
        source (Literal["raw", "processed", "all"]): Type of file information to retrieve.
        media_id (str): The ID of the media information.
        idx (str, optional): Index of the processed file to retrieve(used for pdf, idx is index of the page). Defaults to "-1".

    Returns:
        Union[PartialMediaInfoResponse, MessageResponse]: Partial or complete media information.

    Raises:
        HTTPError: If an error occurs during processing
        MessageResponse:   if the file has not been processed.
    """
    idx = list(map(int, idx.split(",")))
    media_info = MediaInfo.get_or_404(id=media_id)
    # if not media_info.processed_files:
    #     return MessageResponse(
    #         detail="File has not been processed yet. Please try again later.",
    #     )
    return PartialMediaInfoResponse.response_value(
        obj=media_info, source=source, idx=idx
    )
