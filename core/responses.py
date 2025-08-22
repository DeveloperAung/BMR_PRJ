from rest_framework.response import Response

def ok(data=None, message="OK", status=200):
    return Response({"success": True, "message": message, "error": None, "data": data}, status=status)

def fail(error, message="Error", status=400, data=None):
    return Response({"success": False, "message": message, "error": error, "data": data}, status=status)
