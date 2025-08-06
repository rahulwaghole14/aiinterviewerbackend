from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser
from utils.logger import log_user_login, log_user_logout, log_user_registration, ActionLogger

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration with comprehensive logging"""
    try:
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Log successful registration
            log_user_registration(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            ActionLogger.log_user_action(
                user=user,
                action='user_registration',
                details={
                    'registration_data': {
                        'email': user.email,
                        'role': user.role,
                        'company_name': user.company_name
                    },
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
                },
                status='SUCCESS'
            )
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'company_name': user.company_name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            # Log registration failure
            ActionLogger.log_user_action(
                user=None,
                action='user_registration',
                details={
                    'errors': serializer.errors,
                    'attempted_data': request.data,
                    'ip_address': request.META.get('REMOTE_ADDR')
                },
                status='FAILED'
            )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        # Log registration error
        ActionLogger.log_user_action(
            user=None,
            action='user_registration',
            details={
                'error': str(e),
                'attempted_data': request.data,
                'ip_address': request.META.get('REMOTE_ADDR')
            },
            status='FAILED'
        )
        raise

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login with comprehensive logging"""
    try:
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Try to authenticate
            user = authenticate(request, email=email, password=password)
            
            if user:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                
                # Log successful login
                log_user_login(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                ActionLogger.log_user_action(
                    user=user,
                    action='user_login',
                    details={
                        'login_method': 'email_password',
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                        'token_created': created
                    },
                    status='SUCCESS'
                )
                
                return Response({
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role,
                        'company_name': user.company_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Log failed login attempt
                ActionLogger.log_user_action(
                    user=None,
                    action='user_login',
                    details={
                        'attempted_email': email,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                        'reason': 'Invalid credentials'
                    },
                    status='FAILED'
                )
                
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Log login validation failure
            ActionLogger.log_user_action(
                user=None,
                action='user_login',
                details={
                    'errors': serializer.errors,
                    'attempted_data': request.data,
                    'ip_address': request.META.get('REMOTE_ADDR')
                },
                status='FAILED'
            )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        # Log login error
        ActionLogger.log_user_action(
            user=None,
            action='user_login',
            details={
                'error': str(e),
                'attempted_data': request.data,
                'ip_address': request.META.get('REMOTE_ADDR')
            },
            status='FAILED'
        )
        raise

@api_view(['POST'])
def logout_view(request):
    """User logout with comprehensive logging"""
    try:
        if request.user.is_authenticated:
            # Log successful logout
            log_user_logout(
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            ActionLogger.log_user_action(
                user=request.user,
                action='user_logout',
                details={
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
                },
                status='SUCCESS'
            )
            
            # Delete token
            try:
                request.user.auth_token.delete()
            except:
                pass  # Token might not exist
                
            logout(request)
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        else:
            # Log logout attempt by unauthenticated user
            ActionLogger.log_user_action(
                user=None,
                action='user_logout',
                details={
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'reason': 'User not authenticated'
                },
                status='FAILED'
            )
            
            return Response({
                'error': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        # Log logout error
        ActionLogger.log_user_action(
            user=request.user if request.user.is_authenticated else None,
            action='user_logout',
            details={
                'error': str(e),
                'ip_address': request.META.get('REMOTE_ADDR')
            },
            status='FAILED'
        )
        raise

@api_view(['GET', 'PATCH'])
def user_profile_view(request):
    """Get and update user profile"""
    try:
        if request.method == 'GET':
            # Get user profile
            user = request.user
            return Response({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'company_name': user.company_name,
                'username': user.username
            }, status=status.HTTP_200_OK)
            
        elif request.method == 'PATCH':
            # Update user profile
            user = request.user
            data = request.data
            
            # Update allowed fields
            if 'full_name' in data:
                user.full_name = data['full_name']
            if 'company_name' in data:
                user.company_name = data['company_name']
            
            user.save()
            
            return Response({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'company_name': user.company_name,
                'username': user.username
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
