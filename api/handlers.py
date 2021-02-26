import os
import tempfile

from preview_generator.manager import PreviewManager

from api.processor import (
    PreviewManagerJpegProcessor,
    PreviewManagerPdfProcessor,
    PreviewManagerHtmlProcessor,
    PreviewManagerTextProcessor,
)


class PreviewHandlers:
    def __init__(
            self,
            filename,
            binary_file_data,
            width=None,
            height=None,
            need_crop=False,
            extension='jpeg',
    ):
        self.filename = filename
        self.width = width
        self.height = height
        self.binary_file_data = binary_file_data
        self.need_crop = need_crop
        self.processor = self.choice_processor(extension)

    @staticmethod
    def choice_processor(output_extension):
        extensions = {
            'jpeg': PreviewManagerJpegProcessor,
            'pdf': PreviewManagerPdfProcessor,
            'html': PreviewManagerHtmlProcessor,
            'text': PreviewManagerTextProcessor,
        }
        return extensions[output_extension]

    def handle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            file_path = os.path.join(temporary_directory, self.filename)
            file = open(file_path, 'w+b')
            file.write(self.binary_file_data)
            file.close()

            cache_path = os.path.join(temporary_directory, 'cache')

            preview_manager = PreviewManager(cache_path, create_folder=True)
            processor = self.processor(preview_manager=preview_manager, file_path=file_path)
            preview_file_path = processor.process(
                height=self.height,
                width=self.width,
                need_crop=self.need_crop,
            )

            preview_file = open(preview_file_path, 'r+b')
            preview_file_binary_data = preview_file.read()
            preview_file.close()

            return preview_file_path, preview_file_binary_data
