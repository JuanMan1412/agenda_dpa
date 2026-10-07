from django.urls import path

from .views.portal import LocalTokenRefreshView, MyPermissionsView, PortalAccessView
from .administration import UserListView, UserDetailView

urlpatterns = [
    path('usuarios/', UserListView.as_view(), name='usuarios-list'),
    path('usuarios/<int:pk>/', UserDetailView.as_view(), name='usuarios-detail'),
    path('auth/portal-access/', PortalAccessView.as_view(), name='portal-access'),
    path('auth/token/refresh/', LocalTokenRefreshView.as_view(), name='local-token-refresh'),
    path('me/permisos/', MyPermissionsView.as_view(), name='my-permissions'),
]
