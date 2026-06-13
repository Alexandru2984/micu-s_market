from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", getattr(settings, "PERMISSIONS_POLICY", "geolocation=(), microphone=(), camera=()"))
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.setdefault("Cross-Origin-Resource-Policy", getattr(settings, "CROSS_ORIGIN_RESOURCE_POLICY", "same-site"))

        csp_report_only = getattr(settings, "CONTENT_SECURITY_POLICY_REPORT_ONLY", "")
        if csp_report_only:
            response.setdefault("Content-Security-Policy-Report-Only", csp_report_only)

        return response
