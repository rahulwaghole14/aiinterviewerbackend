from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserDataSerializer
from .models import UserData
from utils.hierarchy_permissions import HiringAgencyHierarchyPermission, DataIsolationMixin
from rest_framework import generics, permissions
from .models import UserData
from .serializers import UserDataSerializer


class UserDataViewSet(DataIsolationMixin, viewsets.ModelViewSet):
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer
    permission_classes = [HiringAgencyHierarchyPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return UserData.objects.all()
        elif user.role == "COMPANY":
            return UserData.objects.filter(company_name=user.company_name)
        return UserData.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def create(self, request, *args, **kwargs):
        data = request.data
        creator = request.user
        creator_role = creator.role.upper()

        new_user_role = data.get("role")
        if not new_user_role:
            return Response({"message": "Missing 'role' in request."}, status=status.HTTP_400_BAD_REQUEST)

        new_user_role = new_user_role.upper()

        if not self.has_permission_to_create(creator_role, new_user_role):
            return Response(
                {"message": f"{creator_role} is not allowed to create a {new_user_role}."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Set company_name for Company users
        if creator_role == "COMPANY":
            data['company_name'] = creator.company_name

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.has_object_permission(request, self, instance):
            return Response({'detail': 'You can only edit hiring agency data for your own company.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.has_object_permission(request, self, instance):
            return Response({'detail': 'You can only edit hiring agency data for your own company.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.has_object_permission(request, self, instance):
            return Response({'detail': 'You can only delete hiring agency data for your own company.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def has_permission_to_create(self, creator_role, new_user_role):
        if creator_role == "SUPER_ADMIN":
            return True
        elif creator_role == "ADMIN" and new_user_role in ["HR", "HIRING_MANAGER", "INTERVIEWER", "OTHER", "HIRING AGENCY"]:
            return True
        elif creator_role == "COMPANY" and new_user_role in ["HR", "HIRING_MANAGER", "INTERVIEWER", "OTHER", "HIRING AGENCY"]:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admin can manage all hiring agencies
        if request.user.role == 'ADMIN':
            return True
        
        # Company users can only manage hiring agencies from their own company
        if request.user.role == 'COMPANY':
            return obj.company_name == request.user.company_name
        
        return False


class CreateUserDataView(generics.CreateAPIView):
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer
    permission_classes = [HiringAgencyHierarchyPermission]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # Set company_name for Company users
        if self.request.user.role == "COMPANY":
            serializer.save(company_name=self.request.user.company_name)
        else:
            serializer.save()
