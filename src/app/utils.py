import os
import subprocess
from io import BytesIO
from typing import Callable, Union

from pdf2image import convert_from_bytes
from PIL import Image

from app.database import get_db_session


def db_session_wrapper(func: Callable):
    async def wrapped_func(*args, **kwargs):
        async with get_db_session() as session:
            return await func(*args, **kwargs)
    return wrapped_func


def convert_img_to_png_io(input_image_file: Union[BytesIO, bytes]) -> BytesIO:
    def _resize_img(max_resolution, width, height, img):
        width_scale = max_resolution[0] / width
        height_scale = max_resolution[1] / height
        scale_factor = min(width_scale, height_scale)
        new_width = int(width * scale_factor)
        img = img.resize((new_width, int(height * scale_factor)), Image.LANCZOS)
        result = BytesIO()
        img.save(result, format="PNG")
        return result

    if isinstance(input_image_file, bytes):
        input_image_file = BytesIO(input_image_file)

    max_resolution = (3500, 3500)
    with Image.open(input_image_file) as img:
        width, height = img.size
        if width <= max_resolution[0] and height <= max_resolution[1]:
            output_image_file = BytesIO(input_image_file.getvalue())
        else:
            output_image_file = _resize_img(max_resolution, width, height, img)
    return output_image_file


def convert_pdf_to_png_io(input_pdf_file: Union[BytesIO, bytes]) -> list:
    if isinstance(input_pdf_file, bytes):
        input_pdf_file = BytesIO(input_pdf_file)
    png_pages = []

    pdf_images = convert_from_bytes(input_pdf_file.read(), dpi=300)
    for page_number, pdf_image in enumerate(pdf_images, start=1):
        pdf_image.thumbnail((3500, 3500))
        output_image_file = BytesIO()
        pdf_image.save(output_image_file, format="PNG")
        png_pages.append(output_image_file)

    return png_pages


if __name__ == "__main__":
    with open("tests/images/jpg/1.jpg", "rb") as image_file:
        image_bytes = image_file.read()
        bytesio_object = BytesIO(image_bytes)

    input_image_file = bytesio_object
    output_image_file = convert_img_to_png_io(input_image_file)

    with open("tests/images/output.png", "wb") as f:
        f.write(output_image_file.getvalue())

    with open("tests/images/pdf/1.pdf", "rb") as image_file:
        image_bytes = image_file.read()
        pdf_bytesio_object = BytesIO(image_bytes)

    input_pdf_file = pdf_bytesio_object
    output_png_dict = convert_pdf_to_png_io(input_pdf_file)

    for key, value in output_png_dict.items():
        with open(f"tests/images/pdf/pdf_output_{key}.png", "wb") as f:
            f.write(value.getvalue())
