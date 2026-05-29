from django.urls import path

from .views import (
    register,
    verify_register_otp,
    login_request_otp,
    verify_login_otp,
    session_status,
    me,
    logout_view
)

urlpatterns = [

    path('register/', register),

    path(
        'register/verify/',
        verify_register_otp
    ),

    path(
        'login/',
        login_request_otp
    ),

    path(
        'login/verify/',
        verify_login_otp
    ),

    path('session/', session_status),

    path('me/', me),

    path('logout/', logout_view),
]