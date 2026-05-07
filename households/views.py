from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Household
from .serializers import HouseholdSerializer

class HouseholdCreateView(generics.CreateAPIView):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        household = serializer.save(created_by=self.request.user)
        household.members.add(self.request.user)

class HouseholdDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Household.objects.filter(members=self.request.user)
    
class JoinHouseholdView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('invite_code', '').upper()
        try:
            household = Household.objects.get(invite_code=code)
            household.members.add(request.user)
        except Household.DoesNotExist:
            return Response({'error': 'Invalid invite code'}, status=400)
        
class MyHouseholdView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        household = Household.objects.filter(members=request.user).first()
        if not household:
            return Response({'error': 'Not in a household'}, status=404)
        return Response(HouseholdSerializer(household).data)