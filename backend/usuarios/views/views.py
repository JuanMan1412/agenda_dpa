from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .tokens import AccountActivationTokenGenerator
from ..serializers import PasswordResetSerializer, PasswordResetConfirmSerializer,PasswordResetSerializer
from django.utils.http import urlsafe_base64_decode
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
from ..serializers import CambiarClaveSerializer
from datetime import datetime
from usuarios.models import PasswordHistory
from django.contrib.auth.hashers import check_password
User = get_user_model()


class PasswordResetView(generics.CreateAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError(_('No existe un usuario con ese correo electrónico.'))
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = AccountActivationTokenGenerator().make_token(user)
        #reset_link = f"{request.scheme}://{request.get_host()}/api/login/password/reset/confirm/{uidb64}/{token}/"
        # MEJORAR ESTE CONTROL CUANDO ARROJA UNA EXCEPCION
        return Response(status=status.HTTP_200_OK)


class PasswordResetValidateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, uidb64, token, format=None): 
        try:
            User = get_user_model()
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        token_generator =  AccountActivationTokenGenerator()
        if user is not None and token_generator.check_token(user, token):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        token_generator =  AccountActivationTokenGenerator()
        if user is not None and token_generator.check_token(user, token):
            respuesta = resetPassword(serializer.validated_data['new_password'], user)
            if (respuesta == 'ok'):
                return Response({"detail": _("Contraseña actualizada con éxito.")}, status=status.HTTP_200_OK)
            if (respuesta == 'claveRepetida'):
                    return Response({"error": "La nueva contraseña no puede ser una de las últimas tres contraseñas."}, status=409)
        else:
            return Response({"detail": _("El enlace de restablecimiento de contraseña no es válido o ha expirado.")}, status=status.HTTP_400_BAD_REQUEST)
        

# class Validate_current_password(APIView):
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         user = authenticate(request=request, username=request.user.username, password=request.data['current_password'])
#         if user:
#             return Response(status=status.HTTP_200_OK)
#         else:
#             return Response(status=status.HTTP_400_BAD_REQUEST)

# class  ChangePasswordView(APIView):
#     def get(self, request):
#         return Response(status=status.HTTP_204_NO_CONTENT)

#     def post(self, request):
#         serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.update(request.user, serializer.validated_data)
#             return Response(status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CambiarClaveView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        import re
        serializer = CambiarClaveSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            newPassword = serializer.validated_data['newPassword']
            confirmPassword = serializer.validated_data['confirmPassword']
            if serializer.validated_data['currentPassword']:
                currentPassword = serializer.validated_data['currentPassword']
                if not request.user.check_password(currentPassword):
                    return Response({"error": "La clave actual no es la correcta."}, status=400)
            if newPassword != confirmPassword:
                return Response({"error": "La nueva clave no coincide la confirmacion."}, status=400)
            else:
                if(len(newPassword)<8):
                    return Response({"error": "La nueva clave debe tener 8 o mas caracteres."}, status=400)
                if not(re.search(r'[A-Z]',newPassword)):
                    return Response({"error": "La nueva clave debe tener al menos una letra Mayuscula."}, status=400)
                if not(re.search(r'[0-9]',newPassword)):
                    return Response({"error": "La nueva clave debe tener al menos un Numero."}, status=400)
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=404)
            respuesta = resetPassword(newPassword, user)
            print(respuesta)
            if (respuesta == 'ok'):
                logout(request)
                return Response({"has_changed_password": True, "message": "Clave cambiada exitosamente"}, status=200)
            if (respuesta == 'claveRepetida'):
                    return Response({"error": "La nueva contraseña no puede ser una de las últimas tres contraseñas."}, status=409)
        else:
            return Response(serializer.errors, status=400)

#  Funcion para agregar la clave actual al historial de claves, verificar si la nueva clave se encuentra entre las ultimas tres claves almacenadas y establecer la fecha de ultimo cambio de clave
def resetPassword(newPassword: str, user: object):
    try:

        # Obtengo las ultimas 3 claves
        passwords = PasswordHistory.objects.filter(user=user).order_by('-created_at')[:3]
        # Valido si la nueva clave 
        if passwords:
            for passwd in passwords:
                if check_password(newPassword, passwd.password):
                    print()
                    return 'claveRepetida'
        # Crear el registro de la contraseña actual del usuario
        PasswordHistory.objects.create(
            user = user,
            password = make_password(newPassword),
        )
        # Actualizar la contraseña
        user.password = make_password(newPassword)
        # Actualizo fecha de ultimo cambio de clave
        user.last_password_change = datetime.now()
        user.has_changed_password = True
        user.save()
        return 'ok'
    except Exception as e:
        return 'error'
