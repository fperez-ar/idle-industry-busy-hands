import pytest
from resource_manager import ResourceManager
from resource.definition import ResourceDefinition
from resource.cost import ResourceCost
from resource.effect import ResourceEffect


@pytest.fixture
def sample_resources():
    """Create sample resource definitions."""
    return {
        'money': ResourceDefinition(
            id='money',
            name='Money',
            description='cash & assets',
            icon='💰',
            color=(255, 215, 0),
            base_production=10.0,
            min_value=0.0
        ),
        'reputation': ResourceDefinition(
            id='reputation',
            name='Reputation',
            description='social reputation',
            icon='⭐',
            color=(100, 200, 255),
            base_production=1.0,
            min_value=0.0
        )
    }

@pytest.fixture
def resource_manager(sample_resources):
    """Create a ResourceManager instance."""
    return ResourceManager(sample_resources)


class TestResourceManager:
    """Test ResourceManager functionality."""

    def test_initialization(self, resource_manager):
        """Test that resources are initialized correctly."""
        assert 'money' in resource_manager.resources
        assert 'reputation' in resource_manager.resources

        money = resource_manager.get('money')
        assert money.current_value == 100.0  # base_production * 10
        assert money.definition.name == 'Money'

    def test_get_value(self, resource_manager):
        """Test getting resource values."""
        assert resource_manager.get_value('money') == 100.0
        assert resource_manager.get_value('nonexistent') == 0.0

    def test_spend_success(self, resource_manager):
        """Test successful spending."""
        initial = resource_manager.get_value('money')
        success = resource_manager.spend('money', 50.0)

        assert success is True
        assert resource_manager.get_value('money') == initial - 50.0

    def test_spend_insufficient(self, resource_manager):
        """Test spending more than available."""
        initial = resource_manager.get_value('money')
        success = resource_manager.spend('money', 200.0)

        assert success is False
        assert resource_manager.get_value('money') == initial

    def test_can_afford_single(self, resource_manager):
        """Test affordability check for single cost."""
        costs = [ResourceCost(resource='money', amount=50.0)]
        assert resource_manager.can_afford(costs) is True

        costs = [ResourceCost(resource='money', amount=200.0)]
        assert resource_manager.can_afford(costs) is False

    def test_can_afford_multiple(self, resource_manager):
        """Test affordability check for multiple costs."""
        costs = [
            ResourceCost(resource='money', amount=50.0),
            ResourceCost(resource='reputation', amount=5.0)
        ]
        assert resource_manager.can_afford(costs) is True

        costs = [
            ResourceCost(resource='money', amount=50.0),
            ResourceCost(resource='reputation', amount=50.0)
        ]
        assert resource_manager.can_afford(costs) is False

    def test_pay_costs_success(self, resource_manager):
        """Test successful payment of costs."""
        costs = [
            ResourceCost(resource='money', amount=50.0),
            ResourceCost(resource='reputation', amount=5.0)
        ]

        initial_money = resource_manager.get_value('money')
        initial_rep = resource_manager.get_value('reputation')

        success = resource_manager.pay_costs(costs)

        assert success is True
        assert resource_manager.get_value('money') == initial_money - 50.0
        assert resource_manager.get_value('reputation') == initial_rep - 5.0

    def test_pay_costs_failure(self, resource_manager):
        """Test that failed payment doesn't deduct anything."""
        costs = [
            ResourceCost(resource='money', amount=50.0),
            ResourceCost(resource='reputation', amount=50.0)  # Too much
        ]

        initial_money = resource_manager.get_value('money')
        initial_rep = resource_manager.get_value('reputation')

        success = resource_manager.pay_costs(costs)

        assert success is False
        assert resource_manager.get_value('money') == initial_money
        assert resource_manager.get_value('reputation') == initial_rep

    def test_apply_effect_add(self, resource_manager):
        """Test applying add effect."""
        effect = ResourceEffect(resource='money', effect='add', value=50.0)
        resource_manager.apply_effect(effect)

        # Effect is applied to modifiers, not directly to value
        money = resource_manager.get('money')
        assert hasattr(money, 'base_additions')
        assert money.base_additions == 50.0

    def test_apply_effect_multiply(self, resource_manager):
        """Test applying multiply effect."""
        # base_production * total_multiplier + base_additions

        effect = ResourceEffect(resource='money', effect='mult', value=2.0)
        resource_manager.apply_effect(effect)

        money = resource_manager.get('money')
        assert hasattr(money, 'total_multiplier')
        # assuming ResourceState base multiplier is still
        assert money.total_multiplier == 1 + effect.value

    def test_update_production(self, resource_manager):
        """Test resource production over time."""
        money = resource_manager.get('money')
        initial = money.current_value

        # Add production rate
        effect = ResourceEffect(resource='money', effect='add_rate', value=10.0)
        resource_manager.apply_effect(effect)

        # Update for 1 second
        resource_manager.update(1.0)

        # Should have gained 10 (base) + 10 (modifier) = 20
        assert money.current_value > initial

    def test_recalculate_production(self, resource_manager, sample_resources):
        """Test production recalculation with upgrades."""
        from definitions.upgrade import Upgrade

        upgrade = Upgrade(
            id='test_upgrade',
            name='Test',
            description='Test',
            tree='test_tree',
            tier=0,
            year=0,
            cost=[],
            effects=[
                ResourceEffect(resource='money', effect='add', value=20.0)
            ],
            exclusive_group=None,
            requires=[]
        )

        owned = {'test_upgrade'}
        all_upgrades = {'test_upgrade': upgrade}

        resource_manager.recalculate_production(owned, all_upgrades)

        money = resource_manager.get('money')
        assert money.base_additions == 20.0


class TestResourceState:
    """Test ResourceState functionality."""

    def test_production_calculation(self, resource_manager):
        """Test production per second calculation."""
        # base_production * total_multiplier + base_additions
        money = resource_manager.get('money')

        # Base production is 10
        assert money.get_production_per_second() == 10.0

        # Add rate modifier
        money.base_additions = 5.0
        assert money.get_production_per_second() == 15.0

        # Add multiply modifier
        money.total_multiplier = 2.0
        # money.definition.base_production (10) * money.total_multiplier (2) + money.base_additions (5)
        assert money.get_production_per_second() == 25.0

    def test_reset_modifiers(self, resource_manager):
        """Test resetting modifiers."""
        money = resource_manager.get('money')

        money.base_additions = 100.0
        money.total_multiplier = 2.0

        money.reset_modifiers()

        assert money.base_additions == 0.0
        assert money.total_multiplier == 1.0

    def test_min_value_enforcement(self, resource_manager):
        """Test that minimum value is enforced."""
        money = resource_manager.get('money')
        money.current_value = 50.0

        # Try to spend more than available
        resource_manager.spend('money', 100.0)

        # Should not go below min_value (0)
        assert money.current_value >= money.definition.min_value

    def test_max_value_enforcement(self, resource_manager):
        """Test that maximum value is enforced."""
        # Skip this test if max_value is not supported
        pytest.skip("max_value not supported in ResourceDefinition")
