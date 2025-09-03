from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class EnvelopedPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "OK",
            "error": None,
            "data": {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "results": data,
            },
        })
