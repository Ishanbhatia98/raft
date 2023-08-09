"""Models for the database"""
from contextlib import contextmanager
from functools import wraps
from io import BytesIO
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy import Column, Enum, LargeBinary, String, Text
from sqlalchemy import text as sqlalchemy_text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declared_attr
from typeguard import typechecked

from app.database import db_instance, get_db_session
from app.models.mixin import GetOr404Mixin, UniqueSlugMixin
from app.schema.media_info import CreateMediaInfo, EditMediaInfo
from app.type import FileType
from app.utils import convert_img_to_png_io, convert_pdf_to_png_io

Base = db_instance.base


def string_uuid():
    return str(uuid4())


@typechecked
class BaseSQL(Base):
    __abstract__ = True
    _db_session = None

    @staticmethod
    def session():
        return get_db_session()

    @classmethod
    def empty_table(cls):
        with cls.session() as session:
            session.query(cls).delete()
            session.commit()

    @classmethod
    def create(cls, *args, **kwargs):
        session = cls.session()
        try:
            obj = cls(*args, **kwargs)
            session.add(obj)
            session.commit()
            return obj
        except Exception as e:
            session.rollback()
            raise e

    @classmethod
    def get(cls, id: str):
        session = cls.session()
        try:
            return session.query(cls).filter(cls.id == id).first()
        except Exception as e:
            session.rollback()
            raise e

    @classmethod
    def edit(cls, id: str, **kwargs):
        session = cls.session()
        try:
            session.query(cls).filter(cls.id == id).update(kwargs)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    @classmethod
    def delete(cls, id: str):
        session = cls.session()
        try:
            session.query(cls).filter(cls.id == id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    @classmethod
    def filter(cls, **kwargs):
        session = cls.session()
        try:
            return session.query(cls).filter_by(**kwargs).all()
        except Exception as e:
            session.rollback()
            raise e


class MediaInfo(BaseSQL, GetOr404Mixin, UniqueSlugMixin):
    __tablename__ = "media_info"
    id = Column(String(255), primary_key=True)
    file_name = Column(String, nullable=True)
    raw_file = Column(LargeBinary, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    processed_files = Column(ARRAY(LargeBinary), nullable=True)

    @classmethod
    def create(cls, create_media_info: CreateMediaInfo) -> "MediaInfo":
        return super().create(**create_media_info.db_value, id=string_uuid())

    @classmethod
    def edit(cls, id: str, edit_media_info: EditMediaInfo) -> "MediaInfo":
        cls.get_or_404(id=id)
        return super().edit(id, **edit_media_info.db_value)

    @classmethod
    def delete(cls, id):
        return super().delete(id=id)

    def process_file(self):
        if self.file_type == FileType.PDF:
            processed_files = convert_pdf_to_png_io(self.raw_file)
        else:
            processed_files = [convert_img_to_png_io(self.raw_file)]
        self.edit(
            id=self.id, edit_media_info=EditMediaInfo(processed_files=processed_files)
        )
        return MediaInfo.session().query(MediaInfo).filter_by(id=self.id).first()


if __name__ == "__main__":
    from app.database import db_instance

    # with open("tests/images/pdf/1.pdf", "rb") as image_file:
    #     image_bytes = image_file.read()
    #     pdf_bytesio_object = BytesIO(image_bytes)
    # input_pdf_file = pdf_bytesio_object
    # output_png_dict = convert_pdf_to_png_io(input_pdf_file)
    # output_files = list(output_png_dict.values())
    # create_media_info = CreateMediaInfo(raw_file=input_pdf_file, processed_files=output_files)
    # MediaInfo.create(create_media_info)

    MediaInfo.empty_table()

    # with get_db_session() as session:
    #     media_info = MediaInfo.filter()[0]
    #     print('raw_image', media_info.raw_file)
    #     media_info.process_file()
    #     print(media_info.processed_files)
