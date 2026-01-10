import pytest
from state import GameState
from loader import UpgradeTree
from resource_manager import ResourceManager
from time_system import TimeSystem
from event_manager import EventManager
from definitions.upgrade import Upgrade
from resource.definition import ResourceDefinition
from resource.cost import ResourceCost
from resource.effect import ResourceEffect


@pytest.fixture
def sample_resources():
    """Create sample resources."""
    return {
        'money': ResourceDefinition(
            id='money',
            name='Money',
            description='cash & assets',
            icon='💰',
            color=(255, 215, 0),
            base_production=10.0,
            min_value=0.0
        )
    }


@pytest.fixture
def sample_upgrades():
    """Create sample upgrades."""
    return {
        'upgrade_1': Upgrade(
            id='upgrade_1',
            name='First Upgrade',
            tree='test_tree',
            description='Test',
            tier=0,
            year=0,
            cost=[ResourceCost(resource='money', amount=50.0)],
            effects=[ResourceEffect(resource='money', effect='add_rate', value=5.0)],
            exclusive_group=None,
            requires=[]
        ),
        'upgrade_2': Upgrade(
            id='upgrade_2',
            name='Second Upgrade',
            tree='test_tree',
            description='required upgrade',
            tier=1,
            year=0,
            cost=[ResourceCost(resource='money', amount=100.0)],
            effects=[ResourceEffect(resource='money', effect='add_rate', value=10.0)],
            exclusive_group=None,
            requires=['upgrade_1']
        ),
        'upgrade_3': Upgrade(
            id='upgrade_3',
            name='Future Upgrade',
            tree='test_tree',
            description='requires year',
            tier=0,
            year=5,
            cost=[ResourceCost(resource='money', amount=200.0)],
            effects=[ResourceEffect(resource='money', effect='multiply_rate', value=2.0)],
            exclusive_group=None,
            requires=[]
        ),
        'exclusive_a': Upgrade(
            id='exclusive_a',
            name='Exclusive A',
            tree='test_tree',
            description='test exclusive group',
            tier=0,
            year=0,
            cost=[ResourceCost(resource='money', amount=50.0)],
            effects=[],
            exclusive_group='test_group',
            requires=[]
        ),
        'exclusive_b': Upgrade(
            id='exclusive_b',
            name='Exclusive B',
            tree='test_tree',
            description='test exclusive group',
            tier=0,
            year=0,
            cost=[ResourceCost(resource='money', amount=50.0)],
            effects=[],
            exclusive_group='test_group',
            requires=[]
        )
    }


@pytest.fixture
def game_state(sample_resources, sample_upgrades):
    """Create a GameState instance."""
    resource_manager = ResourceManager(sample_resources)
    time_system = TimeSystem()
    event_manager = EventManager({})

    trees = {
        'test_tree': UpgradeTree(
            id='test_tree',
            name='Test Tree',
            description='Test',
            upgrades=list(sample_upgrades.keys()),
            icon=''
        )
    }

    return GameState(
        resource_manager,
        trees,
        sample_upgrades,
        time_system,
        event_manager
    )


class TestGameState:
    """Test GameState functionality."""

    def test_initialization(self, game_state):
        """Test game state initialization."""
        assert len(game_state.owned_upgrades) == 0
        assert len(game_state.selected_exclusive) == 0
        assert game_state.current_year == 0

    def test_check_requirements_met_no_requirements(self, game_state, sample_upgrades):
        """Test requirements check for upgrade with no requirements."""
        upgrade = sample_upgrades['upgrade_1']
        assert game_state.check_requirements_met(upgrade) is True

    def test_check_requirements_met_with_requirements(self, game_state, sample_upgrades):
        """Test requirements check with prerequisites."""
        upgrade = sample_upgrades['upgrade_2']

        # Should fail without prerequisite
        assert game_state.check_requirements_met(upgrade) is False

        # Should pass with prerequisite
        game_state.owned_upgrades.add('upgrade_1')
        assert game_state.check_requirements_met(upgrade) is True

    def test_check_requirements_year_lock(self, game_state, sample_upgrades):
        """Test year-based requirements."""
        upgrade = sample_upgrades['upgrade_3']

        # Should fail in year 0
        assert game_state.check_requirements_met(upgrade) is False

        # Should pass in year 5
        game_state.time_system.current_year = 5
        assert game_state.check_requirements_met(upgrade) is True

    def test_exclusive_group_available(self, game_state, sample_upgrades):
        """Test exclusive group availability."""
        upgrade_a = sample_upgrades['exclusive_a']
        upgrade_b = sample_upgrades['exclusive_b']

        # Both should be available initially
        assert game_state.check_exclusive_group_available(upgrade_a) is True
        assert game_state.check_exclusive_group_available(upgrade_b) is True

        # Purchase A
        game_state.owned_upgrades.add('exclusive_a')
        game_state.selected_exclusive['test_group'] = 'exclusive_a'

        # A should still be available, B should not
        assert game_state.check_exclusive_group_available(upgrade_a) is True
        assert game_state.check_exclusive_group_available(upgrade_b) is False

    def test_is_upgrade_available(self, game_state, sample_upgrades):
        """Test overall upgrade availability."""
        # upgrade_1 should be available
        assert game_state.is_upgrade_available('upgrade_1') is True

        # upgrade_2 should not (missing prerequisite)
        assert game_state.is_upgrade_available('upgrade_2') is False

        # upgrade_3 should not (year locked)
        assert game_state.is_upgrade_available('upgrade_3') is False

        # Already owned should not be available
        game_state.owned_upgrades.add('upgrade_1')
        assert game_state.is_upgrade_available('upgrade_1') is False

    def test_purchase_upgrade_success(self, game_state):
        """Test successful upgrade purchase."""
        # Give enough money
        game_state.resource_manager.get('money').current_value = 1000.0

        success = game_state.purchase_upgrade('upgrade_1')

        assert success is True
        assert 'upgrade_1' in game_state.owned_upgrades
        assert game_state.resource_manager.get_value('money') == 950.0
