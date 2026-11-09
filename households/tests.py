from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from .models import Household, HouseholdMember

# Create your tests here.

class HouseholdRulesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='x')
        self.member = User.objects.create_user('member', password='x')
        self.hh = Household.objects.create(name='H', created_by=self.owner)
        HouseholdMember.objects.create(household=self.hh, user=self.owner, role='owner')
        HouseholdMember.objects.create(household=self.hh, user=self.member, role='member')

    def api(self, user):
        c = APIClient(); c.force_authenticate(user); return c

    def test_owner_removes_member(self):
        r = self.api(self.owner).delete(f'/api/households/{self.hh.id}/members/{self.member.id}/')
        self.assertEqual(r.status_code, 204)

    def test_member_cannot_remove_owner(self):
        r = self.api(self.member).delete(f'/api/households/{self.hh.id}/members/{self.owner.id}/')
        self.assertEqual(r.status_code, 403)

    def test_member_can_leave(self):
        self.assertEqual(self.api(self.member).post('/api/households/leave/').status_code, 204)
        self.assertFalse(HouseholdMember.objects.filter(user=self.member).exists())

    def test_owner_cannot_leave_while_others_remain(self):
        self.assertEqual(self.api(self.owner).post('/api/households/leave/').status_code, 400)

    def test_last_member_leaving_deletes_household(self):
        self.api(self.member).post('/api/households/leave/')
        self.api(self.owner).post('/api/households/leave/')
        self.assertFalse(Household.objects.filter(pk=self.hh.pk).exists())

    def test_only_owner_sets_budget(self):
        body = {'monthly_budget': 1500000}
        self.assertEqual(self.api(self.member).put('/api/households/me/budget/', body, format='json').status_code, 403)
        self.assertEqual(self.api(self.owner).put('/api/households/me/budget/', body, format='json').status_code, 200)
        self.hh.refresh_from_db()
        self.assertEqual(self.hh.monthly_budget, 1500000)

    def test_member_cannot_rename_household(self):
        r = self.api(self.member).patch(f'/api/households/{self.hh.id}/', {'name': 'X'}, format='json')
        self.assertEqual(r.status_code, 403)