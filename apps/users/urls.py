from django.urls import path

from . import auth_views, views

urlpatterns = [
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("auth/csrf/", auth_views.CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", auth_views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", auth_views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", auth_views.LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", auth_views.CurrentUserView.as_view(), name="auth-me"),
]
