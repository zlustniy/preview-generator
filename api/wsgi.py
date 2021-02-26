#!/usr/bin/env python

import logging

from flask import (
    Flask,
    request,
    make_response,
    jsonify,
    render_template
)
from preview_generator.exception import (
    InputExtensionNotFound,
)
from werkzeug.exceptions import (
    HTTPException,
)

from api.handlers import (
    PreviewHandlers,
)

app = Flask('preview', template_folder='api/templates')


def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    return jsonify(error=error.description, code=code)


for cls in HTTPException.__subclasses__():
    app.register_error_handler(cls, handle_error)


@app.route('/health')
def index():
    return 'ok'


@app.route('/version')
def version_index():
    return weasyprint.__version__


@app.before_first_request
def setup_logging():
    logging.addLevelName(logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
    logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
    logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/preview', methods=['POST'])
def generate():
    filename = request.args.get('filename', 'unnamed', type=str)
    width = request.args.get('width', type=int)
    height = request.args.get('height', type=int)
    need_crop = bool(request.args.get('need_crop', 1, type=int))
    extension = request.args.get('extension', 'jpeg', type=str)

    app.logger.info(
        'POST  /preview?filename=%s&width=%s&height=%s&need_crop=%s&extension=%s' % (
            filename,
            width,
            height,
            need_crop,
            extension,
        ),
    )
    preview = PreviewHandlers(
        filename=filename,
        width=width,
        height=height,
        binary_file_data=request.data,
        extension=extension,
        need_crop=need_crop,
    )
    try:
        preview_file_path, preview_file_binary_data = preview.handle()
        response = make_response(preview_file_binary_data)
        response.headers['Content-Type'] = 'image/jpeg'
        response.headers['Content-Disposition'] = 'inline;filename=%s' % preview_file_path
        app.logger.info(
            ' ==> POST  /preview?filename=%s&width=%s&height=%s&need_crop=%s&extension=%s   ok' % (
                preview_file_path,
                width,
                height,
                need_crop,
                extension,
            ),
        )
        return response
    except InputExtensionNotFound as error:
        return jsonify(error=repr(error), code=400), 400

    except Exception as error:
        return jsonify(error=repr(error), code=400), 400


if __name__ == '__main__':
    app.run()
