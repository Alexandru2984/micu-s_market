import contextvars
import logging
import uuid


request_id_ctx = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


class RequestIdMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or uuid.uuid4().hex
        request.request_id = request_id[:64]
        token = request_id_ctx.set(request.request_id)
        try:
            response = self.get_response(request)
            response[self.response_header] = request.request_id
            return response
        finally:
            request_id_ctx.reset(token)
