from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserDataSerializer
from .models import UserData
from .permissions import IsAdminOrReadOnly  # optional, or use only IsAuthenticated
from rest_framework import generics, permissions
from .models import UserData
from .serializers import UserDataSerializer


class UserDataViewSet(viewsets.ModelViewSet):
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Or just [IsAuthenticated]

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

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if not hasattr(request.user, 'role') or request.user.role != 'COMPANY':
            return Response({'detail': 'Only company users can edit hiring agency data.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not hasattr(request.user, 'role') or request.user.role != 'COMPANY':
            return Response({'detail': 'Only company users can edit hiring agency data.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def has_permission_to_create(self, creator_role, new_user_role):
        if creator_role == "SUPER_ADMIN":
            return True
        elif creator_role == "ADMIN" and new_user_role in ["HR", "HIRING_MANAGER", "INTERVIEWER", "OTHER"]:
            return True
        return False


class CreateUserDataView(generics.CreateAPIView):
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
