from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from loc_detail.models import PublicArt
from .models import Event, EventLocation, EventMembership, EventInvite
from .enums import EventVisibility, MembershipRole, InviteStatus
from .services import create_event
from .forms import EventForm


class EventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.location = PublicArt.objects.create(
            title='Test Art',
            artist_name='Test Artist',
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_event_slug_generation(self):
        """Test that event slug is auto-generated"""
        future_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title='Test Event',
            host=self.user,
            start_time=future_time,
            start_location=self.location
        )
        
        self.assertIsNotNone(event.slug)
        self.assertIn('test-event', event.slug)
    
    def test_event_str(self):
        """Test event string representation"""
        future_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title='Test Event',
            host=self.user,
            start_time=future_time,
            start_location=self.location
        )
        
        expected = f"Test Event by {self.user.username}"
        self.assertEqual(str(event), expected)


class EventServiceTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='testpass')
        self.invitee1 = User.objects.create_user(username='invitee1', password='testpass')
        self.invitee2 = User.objects.create_user(username='invitee2', password='testpass')
        
        self.location1 = PublicArt.objects.create(
            title='Art 1',
            artist_name='Artist 1',
            latitude=40.7128,
            longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title='Art 2',
            artist_name='Artist 2',
            latitude=40.7589,
            longitude=-73.9851
        )
    
    def test_create_event_basic(self):
        """Test creating a basic event"""
        future_time = timezone.now() + timedelta(days=1)
        
        form_data = {
            'title': 'Test Event',
            'start_time': future_time,
            'start_location': self.location1,
            'visibility': EventVisibility.PUBLIC_OPEN,
            'description': 'Test description'
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        event = create_event(
            host=self.host,
            form=form,
            locations=[],
            invites=[]
        )
        
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.host, self.host)
        self.assertEqual(event.visibility, EventVisibility.PUBLIC_OPEN)
        
        # Check host membership created
        self.assertTrue(
            EventMembership.objects.filter(
                event=event,
                user=self.host,
                role=MembershipRole.HOST
            ).exists()
        )
    
    def test_create_event_with_locations(self):
        """Test creating event with additional locations"""
        future_time = timezone.now() + timedelta(days=1)
        
        form_data = {
            'title': 'Multi-Stop Event',
            'start_time': future_time,
            'start_location': self.location1,
            'visibility': EventVisibility.PUBLIC_OPEN,
            'description': ''
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        event = create_event(
            host=self.host,
            form=form,
            locations=[self.location2.id],
            invites=[]
        )
        
        # Check location created
        self.assertEqual(event.locations.count(), 1)
        self.assertEqual(event.locations.first().location, self.location2)
        self.assertEqual(event.locations.first().order, 1)
    
    def test_create_event_with_invites(self):
        """Test creating event with invites"""
        future_time = timezone.now() + timedelta(days=1)
        
        form_data = {
            'title': 'Private Event',
            'start_time': future_time,
            'start_location': self.location1,
            'visibility': EventVisibility.PRIVATE,
            'description': ''
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        event = create_event(
            host=self.host,
            form=form,
            locations=[],
            invites=[self.invitee1.id, self.invitee2.id]
        )
        
        # Check invites created
        self.assertEqual(event.invites.count(), 2)
        self.assertTrue(
            EventInvite.objects.filter(
                event=event,
                invitee=self.invitee1,
                status=InviteStatus.PENDING
            ).exists()
        )
        
        # Check invited memberships created
        self.assertEqual(event.memberships.filter(role=MembershipRole.INVITED).count(), 2)


class EventFormTests(TestCase):
    def setUp(self):
        self.location = PublicArt.objects.create(
            title='Test Art',
            artist_name='Test Artist',
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        future_time = timezone.now() + timedelta(days=1)
        
        form = EventForm(data={
            'title': 'Valid Event',
            'start_time': future_time,
            'start_location': self.location.id,
            'visibility': EventVisibility.PUBLIC_OPEN,
            'description': 'Valid description'
        })
        
        self.assertTrue(form.is_valid())
    
    def test_form_past_time_invalid(self):
        """Test form rejects past datetime"""
        past_time = timezone.now() - timedelta(days=1)
        
        form = EventForm(data={
            'title': 'Past Event',
            'start_time': past_time,
            'start_location': self.location.id,
            'visibility': EventVisibility.PUBLIC_OPEN,
            'description': ''
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)

