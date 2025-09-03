from rest_framework.permissions import BasePermission

class HasRoleOrPerm(BasePermission):
    """
    Allow if user has ANY of required roles (view.required_roles)
    or ANY of required Django permissions codenames (view.required_perms).
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        roles_req = getattr(view, "required_roles", [])
        perms_req = getattr(view, "required_perms", [])
        if roles_req:
            if user.roles.filter(name__in=roles_req, is_active=True).exists():
                return True
        if perms_req:
            if user.has_perms(perms_req):
                return True
        # default deny if requirements declared
        return not (roles_req or perms_req)
