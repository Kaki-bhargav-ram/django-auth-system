import random

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.decorators import authentication_classes
from rest_framework.authentication import SessionAuthentication

from drf_yasg.utils import swagger_auto_schema

from .models import OTP
from .serializers import RegisterSerializer
from .verify_serializer import VerifyOTPSerializer
from .login_serializer import LoginSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Keep session-based auth, but skip DRF's CSRF enforcement for
    API endpoints that are explicitly designed to be CSRF-exempt.
    """

    def enforce_csrf(self, request):
        return


# =========================
# REGISTER
# =========================

@swagger_auto_schema(method='post', request_body=RegisterSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def register(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.save()

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
            otp=otp,
            purpose='register'
        )

        send_mail(
            'Registration OTP',
            f'Your registration OTP is: {otp}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Registration OTP sent"},
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# VERIFY REGISTER OTP
# =========================

@swagger_auto_schema(method='post', request_body=VerifyOTPSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def verify_register_otp(request):

    serializer = VerifyOTPSerializer(data=request.data)

    if serializer.is_valid():

        email = serializer.validated_data['email']
        otp   = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)

            otp_obj = OTP.objects.filter(
                user=user,
                otp=otp,
                purpose='register'
            ).last()

            if not otp_obj:
                return Response(
                    {"error": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Activate user
            user.is_active = True
            user.save()

            # Delete used OTP
            otp_obj.delete()

            # Log user in — creates session cookie
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return Response(
                {"message": "Registration successful"},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# LOGIN REQUEST OTP
# =========================

@swagger_auto_schema(method='post', request_body=LoginSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def login_request_otp(request):

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Get user directly — bypass authenticate() which blocks inactive users
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check password manually
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate and send OTP
        otp = str(random.randint(100000, 999999))

        OTP.objects.create(
            user=user,
            otp=otp,
            purpose='login'
        )
        print("LOGIN USER AUTHENTICATED")
        print(user.email)
        print("SENDING OTP...")
        try:
            send_mail(
                'Login OTP',
                f'Your OTP is {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            print("EMAIL SENT SUCCESSFULLY")

        except Exception as e:
            print("EMAIL ERROR:", str(e))

            return Response(
                {"error": str(e)},
                status=500
            )

        return Response(
            {
                "message": "Login OTP sent",
                "email": user.email
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# VERIFY LOGIN OTP
# =========================

@swagger_auto_schema(method='post', request_body=VerifyOTPSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def verify_login_otp(request):

    serializer = VerifyOTPSerializer(data=request.data)

    if serializer.is_valid():

        email = serializer.validated_data['email']
        otp   = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)

            otp_obj = OTP.objects.filter(
                user=user,
                otp=otp,
                purpose='login'
            ).last()

            if not otp_obj:
                return Response(
                    {"error": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete used OTP
            otp_obj.delete()

            # Activate user if not already active
            if not user.is_active:
                user.is_active = True
                user.save()

            # Log user in — creates session cookie
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return Response(
                {"message": "Login successful"},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# CURRENT USER
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):

    user = request.user

    return Response({
        "id":       user.id,
        "username": user.username,
        "email":    user.email,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def session_status(request):
    """
    Frontend-friendly auth status endpoint.
    Always returns 200 so initial app load does not look like an error
    in browser devtools when user is simply logged out.
    """

    if request.user.is_authenticated:
        return Response({
            "authenticated": True,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            }
        }, status=status.HTTP_200_OK)

    return Response({"authenticated": False}, status=status.HTTP_200_OK)


# =========================
# LOGOUT
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def logout_view(request):

    logout(request)

    response = Response(
        {"message": "Logged out successfully"},
        status=status.HTTP_200_OK
    )

    response.delete_cookie('sessionid')

    return response