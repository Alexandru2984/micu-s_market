import contextvars
import logging
import re
import uuid

request_id_ctx = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


class RequestIdMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"
    request_id_pattern = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name, "")
        if not self.request_id_pattern.fullmatch(request_id):
            request_id = uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_ctx.set(request.request_id)
        try:
            response = self.get_response(request)
            response[self.response_header] = request.request_id
            return response
        finally:
            request_id_ctx.reset(token)
