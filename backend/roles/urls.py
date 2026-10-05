from django.urls import include, path
from rest_framework import routers

from .apis import RolViewSet

router = routers.DefaultRouter()
router.register(r"roles", RolViewSet, basename="roles")

urlpatterns = [
    path("", include(router.urls)),
]
