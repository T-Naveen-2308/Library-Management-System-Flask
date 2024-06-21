from flask import Blueprint
from library_app.errors.utils import render_error_template

errors = Blueprint("errors", __name__)

error_codes = [400, 401, 403, 404, 429, 500, 503]

for error_code in error_codes:
    @errors.app_errorhandler(error_code)
    def handle_error(error, code=error_code):
        return render_error_template(code)