from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Household, HouseholdMember
from .serializers import HouseholdSerializer

class HouseholdCreateView(generics.CreateAPIView):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            household = serializer.save(created_by=request.user)
            HouseholdMember.objects.create(
                household=household,
                user=request.user,
                role=HouseholdMember.OWNER
            )
            return Response(HouseholdSerializer(household).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            HouseholdMember.objects.get_or_create(
                household=household,
                user=request.user,
                defaults={'role':HouseholdMember.MEMBER}
            )
            return Response(HouseholdSerializer(household).data)
        except Household.DoesNotExist:
            return Response({'error': 'Invalid invite code'}, status=400)
        
class MyHouseholdView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        household = Household.objects.filter(members=request.user).first()
        if not household:
            return Response({'error': 'Not in a household'}, status=404)
        return Response(HouseholdSerializer(household).data)