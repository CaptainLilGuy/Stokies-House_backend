from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, DeviceToken
from .serializers import UserSerializer, RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print("Incoming data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation error = ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class DeviceTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = str(request.data.get('token', '')).strip()
        if not token:
            return Response({'token': 'This field is required.'}, status=400)
        platform = request.data.get('platform', DeviceToken.Platform.ANDROID)
        if platform not in DeviceToken.Platform.ANDROID:
            platform = DeviceToken.Platform.ANDROID
        # Upsert by token: if another user was last on this phone, the token moves to the current user
        DeviceToken.objects.update_or_create(
            token=token, defaults={'user': request.user, 'platform': platform})
        return Response({'status': 'registered'})

    def delete(self, request):
        token = str(request.data.get('token', '')).strip()
        DeviceToken.objects.filter(token=token, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)