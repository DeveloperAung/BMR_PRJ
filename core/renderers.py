from rest_framework.renderers import JSONRenderer

class EnvelopedJSONRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = getattr(response, "status_code", 200)
        if isinstance(data, dict) and {"success","message","error","data"}.issubset(data.keys()):
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {
            "success": 200 <= status_code < 300,
            "message": "",
            "error": None if 200 <= status_code < 300 else data,
            "data": data if 200 <= status_code < 300 else None,
        }
        return super().render(envelope, accepted_media_type, renderer_context)
