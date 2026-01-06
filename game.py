import pyglet
from typing import Dict
from pyglet.window import Window, mouse, key

from config import load_config, get_config
from loader import load_resources, load_upgrades, UpgradeTree, Upgrade
from resources import ResourceManager
from state import GameState
from time_system import TimeSystem, TimeControlUI
from ui.tree_view import InteractiveTreeView
from ui.resource_panel import ResourcePanel
from ui.tree_selector import TreeSelector


class Game(Window):
    """Main game window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load configuration first
        self.game_config = load_config('data/config.yml')
        print(f"Starting game with year: {self.game_config.get('time.start_year')}")

        # Load data
        self.resource_definitions = load_resources('data/resources.yml')
        self.trees, self.all_upgrades = load_upgrades('data/upgrades.yml')

        # Initialize time system (will use config internally)
        self.time_system = TimeSystem()

        # Initialize systems
        self.resource_manager = ResourceManager(self.resource_definitions)
        self.game_state = GameState(
            self.resource_manager,
            self.trees,
            self.all_upgrades,
            self.time_system
        )

        # Add year change listener
        self.time_system.add_year_listener(self.on_year_changed)

        # Batch for misc drawing
        self.batch = pyglet.graphics.Batch()

        # Create UI components
        self._create_ui()

        # Schedule update
        pyglet.clock.schedule_interval(self.update, 1/60.0)

    def _create_ui(self):
        """Initialize all UI components."""
        # Layout constants
        sidebar_width = 300
        time_panel_height = 90
        resource_panel_height = 150

        # Tree selector (left side - full height)
        self.tree_selector = TreeSelector(
            x=0,
            y=0,
            width=sidebar_width,
            height=self.height,
            trees=self.trees
        )

        # Time control panel (top-right)
        self.time_control = TimeControlUI(
            x=self.width - 250,
            y=self.height - time_panel_height - 10,
            width=240,
            time_system=self.time_system
        )

        # Resource panel (auto-extending, centered at top)
        # max_width is the available space (full width minus some margin)
        available_width = self.width - 20  # 10px margin on each side

        self.resource_panel = ResourcePanel(
            x=10,  # Will be recalculated by auto-extend
            y=self.height - resource_panel_height - 10,
            width=1000,  # Base width (will auto-extend)
            height=resource_panel_height,
            resource_manager=self.resource_manager,
            max_width=available_width
        )

        # Tree views (main area)
        self.tree_views: Dict[str, InteractiveTreeView] = {}
        tree_area_x = sidebar_width
        tree_area_width = self.width - sidebar_width

        for tree_id, tree in self.trees.items():
            self.tree_views[tree_id] = InteractiveTreeView(
                x=tree_area_x,
                y=0,
                width=tree_area_width,
                height=self.height,
                tree=tree,
                game_state=self.game_state
            )

    def on_year_changed(self, new_year: int):
        """Called when the year changes."""
        print(f"📅 Year changed to: {new_year}")

        # Check if any new upgrades became available
        newly_unlocked = []
        for upgrade_id, upgrade in self.all_upgrades.items():
            if (upgrade.year == new_year and
                upgrade_id not in self.game_state.owned_upgrades):
                newly_unlocked.append(upgrade.name)

        if newly_unlocked:
            print(f"  🔓 New upgrades unlocked: {', '.join(newly_unlocked)}")

    def update(self, dt: float):
        """Main update loop."""
        # Update time system
        self.time_system.update(dt)
        time_scale = self.time_system.get_effective_time_scale()

        # Update game state
        self.game_state.update(dt, time_scale)

        # Update UI
        self.resource_panel.update()
        self.time_control.update()

        # Update active tree view
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            # send time to tree view
            self.tree_views[active_tree_id].update(dt)

            available = self.game_state.get_available_upgrade_ids()
            self.tree_views[active_tree_id].update_nodes(
                self.game_state.owned_upgrades,
                available,
                self.resource_manager
            )

    def on_draw(self):
        """Render the game."""
        self.clear()

        # Draw active tree view (background)
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].draw(self.batch)

        # Draw UI panels on top
        self.tree_selector.draw()
        self.resource_panel.draw()
        self.time_control.draw()

        # Draw instructions
        instructions = pyglet.text.Label(
            "Left-click: Purchase | Right-drag: Pan | Scroll: Zoom | Space: Pause | ESC: Quit",
            x=self.width - 10,
            y=10,
            anchor_x='right',
            font_size=9,
            color=(150, 150, 150, 255)
        )
        instructions.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse clicks."""
        # Check tree selector
        selected_tree = self.tree_selector.on_mouse_press(x, y)
        if selected_tree:
            return

        # Check time control buttons
        time_action = self.time_control.on_mouse_press(x, y)
        if time_action:
            self.time_control.handle_action(time_action)
            return

        # Check active tree view
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            clicked_upgrade = self.tree_views[active_tree_id].on_mouse_press(
                x, y, button, modifiers
            )

            if clicked_upgrade and button == mouse.LEFT:
                # Attempt to purchase
                success = self.game_state.purchase_upgrade(clicked_upgrade)
                if success:
                    upgrade = self.all_upgrades.get(clicked_upgrade)
                    print(f"✓ Purchased: {upgrade.name if upgrade else clicked_upgrade}")
                else:
                    upgrade = self.all_upgrades.get(clicked_upgrade)
                    if upgrade:
                        if clicked_upgrade in self.game_state.owned_upgrades:
                            print(f"✗ Already owned: {upgrade.name}")
                        elif upgrade.year > self.game_state.current_year:
                            print(f"✗ Not yet available (Year {upgrade.year}): {upgrade.name}")
                        elif not self.game_state.check_requirements_met(upgrade):
                            print(f"✗ Requirements not met: {upgrade.name}")
                        elif not self.game_state.check_exclusive_group_available(upgrade):
                            print(f"✗ Exclusive group blocked: {upgrade.name}")
                        elif not self.resource_manager.can_afford(upgrade.cost):
                            print(f"✗ Cannot afford: {upgrade.name}")
                        else:
                            print(f"✗ Cannot purchase: {upgrade.name}")

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Handle mouse drag for panning."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            # Cancel tooltip while dragging
            self.tree_views[active_tree_id].tooltip.cancel_hover()
            self.tree_views[active_tree_id].hovered_node_id = None

            self.tree_views[active_tree_id].on_mouse_drag(
                x, y, dx, dy, buttons, modifiers
            )

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zooming and scrolling panels."""
        # Check if scrolling over resource panel first
        if self.resource_panel.on_mouse_scroll(x, y, scroll_x, scroll_y):
            return  # Resource panel handled the scroll, don't pass to other components

        # Check if scrolling over tree selector
        self.tree_selector.on_mouse_scroll(x, y, scroll_x, scroll_y)

        # Check active tree view for zoom
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse motion for tooltips."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_motion(x, y)

    def on_key_press(self, symbol: int, modifiers: int):
        """Handle keyboard input."""
        # ESC to quit
        if symbol == key.ESCAPE:
            print("Exiting game...")
            self.close()
            return

        # Space bar to pause/unpause
        if symbol == key.SPACE:
            paused = self.time_system.toggle_pause()
            print(f"⏸ Time {'PAUSED' if paused else 'RESUMED'}")

        # Plus/Minus keys to adjust speed
        elif symbol == key.PLUS or symbol == key.EQUAL:
            new_speed = self.time_system.time_multiplier * 2
            self.time_system.set_speed(new_speed)
            print(f"⏩ Speed: {self.time_system.time_multiplier:.1f}x")

        elif symbol == key.MINUS:
            new_speed = self.time_system.time_multiplier / 2
            self.time_system.set_speed(new_speed)
            print(f"⏪ Speed: {self.time_system.time_multiplier:.1f}x")

        # Number keys 1-5 to set specific speeds
        elif symbol == key._1:
            self.time_system.set_speed(0.5)
            print(f"Speed: {self.time_system.time_multiplier:.1f}x")
        elif symbol == key._2:
            self.time_system.set_speed(1.0)
            print(f"Speed: {self.time_system.time_multiplier:.1f}x")
        elif symbol == key._3:
            self.time_system.set_speed(2.0)
            print(f"Speed: {self.time_system.time_multiplier:.1f}x")
        elif symbol == key._4:
            self.time_system.set_speed(4.0)
            print(f"Speed: {self.time_system.time_multiplier:.1f}x")
        elif symbol == key._5:
            self.time_system.set_speed(8.0)
            print(f"Speed: {self.time_system.time_multiplier:.1f}x")

        # R to reset camera on active tree
        elif symbol == key.R:
            active_tree_id = self.tree_selector.active_tree_id
            if active_tree_id and active_tree_id in self.tree_views:
                self.tree_views[active_tree_id]._center_camera()
                print("📷 Camera reset")

        # S to show statistics
        elif symbol == key.S:
            stats = self.game_state.get_statistics()
            print("\n" + "="*50)
            print("📊 GAME STATISTICS")
            print("="*50)
            print(f"Current Year: {stats['current_year']}")
            print(f"Owned Upgrades: {stats['owned_upgrades']}/{stats['total_upgrades']} ({stats['completion_percentage']:.1f}%)")
            print(f"Available Upgrades: {stats['available_upgrades']}")
            if stats['next_unlock_year']:
                print(f"Next Unlock: Year {stats['next_unlock_year']} ({stats['years_until_next_unlock']} years)")
            print("\nTree Progress:")
            for tree_id, tree_stat in stats['tree_statistics'].items():
                tree_name = self.trees[tree_id].name
                print(f"  {tree_name}: {tree_stat['owned']}/{tree_stat['total']} ({tree_stat['percentage']:.1f}%)")
            print("="*50 + "\n")

        # D for debug info
        elif symbol == key.D:
            print("\n" + "="*50)
            print("🔧 DEBUG INFO")
            print("="*50)
            print(f"Active Tree: {self.tree_selector.active_tree_id}")
            print(f"Time Paused: {self.time_system.paused}")
            print(f"Time Speed: {self.time_system.time_multiplier}x")
            print(f"Year Progress: {self.time_system.get_progress_percent():.1f}%")
            print("\nResources:")
            for res_id, res_state in self.resource_manager.resources.items():
                print(f"  {res_state.definition.name}: {res_state.current_value:.2f} ({res_state.get_production_per_second():.2f}/s)")
            print("="*50 + "\n")

        # H for help
        elif symbol == key.H:
            print("\n" + "="*50)
            print("❓ KEYBOARD SHORTCUTS")
            print("="*50)
            print("ESC      - Quit game")
            print("Space    - Pause/Resume time")
            print("+/=      - Increase time speed")
            print("-        - Decrease time speed")
            print("1-5      - Set specific time speeds")
            print("R        - Reset camera to center")
            print("S        - Show statistics")
            print("D        - Show debug info")
            print("H        - Show this help")
            print("\nMouse Controls:")
            print("Left-click     - Purchase upgrade")
            print("Right-drag     - Pan camera")
            print("Scroll wheel   - Zoom in/out (or scroll panels)")
            print("="*50 + "\n")

    def on_resize(self, width: int, height: int):
        """Handle window resize."""
        super().on_resize(width, height)

        # Recreate UI with new dimensions
        self._create_ui()
