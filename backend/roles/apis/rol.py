from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from utils.portal_auth import PORTAL_ROLE_ADMINISTRADOR, RolePermissionByActionMixin

from ..models import Rol
from ..serializers import RolSerializer


class RolViewSet(RolePermissionByActionMixin, viewsets.ModelViewSet):
    queryset = Rol.objects.all().order_by("descripcion")
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAuthenticated]
    role_permission_map = {
        "list": {PORTAL_ROLE_ADMINISTRADOR},
        "retrieve": {PORTAL_ROLE_ADMINISTRADOR},
        "create": {PORTAL_ROLE_ADMINISTRADOR},
        "update": {PORTAL_ROLE_ADMINISTRADOR},
        "partial_update": {PORTAL_ROLE_ADMINISTRADOR},
        "destroy": {PORTAL_ROLE_ADMINISTRADOR},
        "busqueda": {PORTAL_ROLE_ADMINISTRADOR},
    }

    @action(detail=False, methods=["get"], url_path=r"busqueda/(?P<descripcion>[a-zA-Z0-9 ]+)", name="Busqueda")
    def busqueda(self, request, descripcion, *args, **kwargs):
        queryset = Rol.objects.filter(descripcion=descripcion).first()
        if queryset is None:
            return Response({"error": "No se encuentra el rol que esta solicitando"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=False)
        return Response(serializer.data)
