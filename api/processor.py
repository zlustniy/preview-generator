from __future__ import annotations

from typing import Tuple

from PIL import Image
from preview_generator.manager import PreviewManager


class PreviewManagerProcessor:
    def __init__(self, preview_manager: PreviewManager, file_path: str):
        self.preview_manager = preview_manager
        self.file_path = file_path

    def process(self, **kwargs):
        raise NotImplementedError


class PreviewManagerJpegProcessor(PreviewManagerProcessor):
    HEIGHT = 256
    WIDTH = HEIGHT

    def get_parameters_for_preview_generator(self, height: int, width: int) -> Tuple[int, int]:
        """
        Метод возвращает высоту и ширину, к которым мы будем стремиться при получении
        preview-изображения: max(height, width) x max(height, width).

        :param height: Высота, переданная клиентом.
        :param width: Ширина, переданная клиентом.
        :return: Ширина, Высота.
        """
        attributes = [
            self.WIDTH,
            self.HEIGHT,
            height,
            width,
        ]

        attrib = max([attr for attr in attributes if attr is not None])
        preview_generator_width = attrib
        preview_generator_height = attrib

        return preview_generator_width, preview_generator_height

    def process(self, height: int, width: int, need_crop: bool) -> str:
        """

        :param height: Высота, переданная клиентом.
        :param width: Ширина, переданная клиентом.
        :param need_crop: Мы всегда стараемся получить preview-изображение с правильными пропорциями. Флаг указывает
                          о необходимости обрезать изображение, чтобы привести его к параметрам, переданным клиентом.
        :return: Путь к файлу preview-изображения.
        """
        preview_generator_width, preview_generator_height = self.get_parameters_for_preview_generator(height, width)

        preview_file_path = self.preview_manager.get_jpeg_preview(
            file_path=self.file_path,
            width=preview_generator_width,
            height=preview_generator_height,
        )
        if height is not None or width is not None:
            self._resize(
                file_path=preview_file_path,
                height=height,
                width=width,
                need_crop=need_crop,
            )
        return preview_file_path

    def _resize(self, file_path: str, height: int, width: int, need_crop: bool) -> Image:
        """
        Мы не знаем исходных размеров полученного изображения, с которым внутри себя работает пакет preview_generator.
        Исходные размеры сложно посчитать где-то отдельно, т.к. клиент может передать файлы pdf, xls и т.д.
        Задумка в том, что мы должны после обработки в preview_generator получить минимально большую картинку,
        которую будем дальше уменьшать и обрезать под требования клиента.

        Метод изменяет размер изображения. В большинстве случаев, после обработки в preview_generator
        мы получаем картинку с правильным соотношением, но не строго в размерах, которые передал клиент.

        :param file_path: Путь к файлу preview-изображения после обработки в preview_generator.
        :param height:  Высота, переданная клиентом.
        :param width: Ширина, переданная клиентом.
        :param need_crop: Необходимо обрезать изображение, чтобы привести его к параметрам, переданным клиентом.
        :return: PIL.Image.Image object
        """
        with Image.open(file_path) as image:
            attributes = [
                (height, self.resize_height_strategy),
                (width, self.resize_width_strategy),
            ]
            attrib, strategy = max([attr for attr in attributes if attr[0] is not None], key=lambda x: x[0])
            if attrib is not None:
                min_possible_width, min_possible_height = strategy(attrib, image)
                image = image.resize((min_possible_width, min_possible_height), Image.ANTIALIAS)
                if need_crop and height is not None and width is not None:
                    image = self.crop(
                        image=image,
                        width=min_possible_width,
                        height=min_possible_height,
                        new_width=width,
                        new_height=height,
                    )
                image.save(file_path)
                return image

    @staticmethod
    def resize_width_strategy(width: int, image: Image) -> Tuple[int, int]:
        """
        Метод рассчитывает пропорциональную высоту для переданного изображения относительно ширины.


        :param width: Необходимая ширина.
        :param image: Изображение, для которого необходимо найти пропорциональную высоту.
        :return: Пропорциональные ширина и высота.
        """
        ratio = (width / float(image.size[0]))
        height = int((float(image.size[1]) * float(ratio)))
        return width, height

    @staticmethod
    def resize_height_strategy(height: int, image: Image) -> Tuple[int, int]:
        """
        Метод рассчитывает пропорциональную ширину для переданного изображения относительно высоты.


        :param height: Необходимая высота.
        :param image: Изображение, для которого необходимо найти пропорциональную ширину.
        :return: Пропорциональные ширина и высота.
        """
        ratio = (height / float(image.size[1]))
        width = int((float(image.size[0]) * float(ratio)))
        return width, height

    @staticmethod
    def crop(image: Image, width: int, height: int, new_width: int, new_height: int) -> Image:
        """
        Метод обрезает по краям изображение до нужных значений.


        :param image: Изображение, которое необходимо обрезать.
        :param width: Исходная ширина изображения.
        :param height: Исходная высота изображения.
        :param new_width: Необходимая ширина изображения.
        :param new_height: Необходимая высота изображения.
        :return: Обрезанное изображение
        """

        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        image = image.crop((left, top, right, bottom))
        return image


class PreviewManagerPdfProcessor(PreviewManagerProcessor):
    def process(self, **kwargs):
        preview_file_path = self.preview_manager.get_pdf_preview(
            file_path=self.file_path,
        )
        return preview_file_path


class PreviewManagerHtmlProcessor(PreviewManagerProcessor):
    def process(self, **kwargs):
        preview_file_path = self.preview_manager.get_html_preview(
            file_path=self.file_path,
        )
        return preview_file_path


class PreviewManagerTextProcessor(PreviewManagerProcessor):
    def process(self, **kwargs):
        preview_file_path = self.preview_manager.get_text_preview(
            file_path=self.file_path,
        )
        return preview_file_path
