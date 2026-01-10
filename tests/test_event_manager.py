import pytest
from event_manager import EventManager
from event_manager import Event, EventChoice
from resource.cost import ResourceCost
from resource.effect import ResourceEffect


@pytest.fixture
def sample_events():
    """Create sample events."""
    return {
        'year_event': Event(
            id='year_event',
            title='Year Event',
            description='Test',
            icon='🎉',
            trigger_type='year',
            trigger_value=5,
            choices=[
                EventChoice(
                    id='choice_1',
                    text='Choice 1',
                    description='Test',
                    cost=[],
                    effects=[]
                )
            ]
        ),
        'upgrade_event': Event(
            id='upgrade_event',
            title='Upgrade Event',
            description='Test',
            icon='🎯',
            trigger_type='upgrades',
            trigger_value=['upgrade_1', 'upgrade_2'],
            choices=[
                EventChoice(
                    id='choice_1',
                    text='Choice 1',
                    description='Test',
                    cost=[],
                    effects=[]
                )
            ]
        )
    }


@pytest.fixture
def event_manager(sample_events):
    """Create an EventManager instance."""
    return EventManager(sample_events)


class TestEventManager:
    """Test EventManager functionality."""

    def test_initialization(self, event_manager):
        """Test event manager initialization."""
        assert len(event_manager.events) == 2
        assert event_manager.pending_event is None

    def test_year_trigger(self, event_manager):
        """Test year-based event trigger."""
        # Should not trigger in year 0
        event = event_manager.check_triggers(0, set())
        assert event is None

        # Should trigger in year 5
        event = event_manager.check_triggers(5, set())
        assert event is not None
        assert event.id == 'year_event'
        assert event.triggered is True

    def test_upgrade_trigger(self, event_manager):
        """Test upgrade-based event trigger."""
        # Should not trigger with no upgrades
        event = event_manager.check_triggers(0, set())
        assert event is None

        # Should not trigger with only one upgrade
        event = event_manager.check_triggers(0, {'upgrade_1'})
        assert event is None

        # Should trigger with both upgrades
        event = event_manager.check_triggers(0, {'upgrade_1', 'upgrade_2'})
        assert event is not None
        assert event.id == 'upgrade_event'

    def test_event_only_triggers_once(self, event_manager):
        """Test that events only trigger once."""
        # Trigger the event
        event1 = event_manager.check_triggers(5, set())
        assert event1 is not None

        # Try to trigger again
        event2 = event_manager.check_triggers(5, set())
        assert event2 is None  # Should not trigger again

    def test_pending_event_blocks_new_triggers(self, event_manager):
        """Test that pending event blocks new triggers."""
        # Trigger first event
        event1 = event_manager.check_triggers(5, set())
        assert event1 is not None

        # Try to trigger second event (should be blocked)
        event2 = event_manager.check_triggers(10, {'upgrade_1', 'upgrade_2'})
        assert event2 is None

    def test_clear_pending(self, event_manager):
        """Test clearing pending event."""
        event = event_manager.check_triggers(5, set())
        assert event_manager.pending_event is not None

        event_manager.clear_pending()
        assert event_manager.pending_event is None
