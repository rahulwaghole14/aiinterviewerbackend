from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserDataSerializer
from .models import UserData


@api_view(['POST'])
def add_user(request):
    serializer = UserDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': 'User data saved successfully!',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    return Response(
        {
            'message': 'Failed to save user data.',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )
