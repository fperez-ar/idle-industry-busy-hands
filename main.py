import pyglet
from game import Game
from config import load_config

if __name__ == '__main__':

    config = load_config('data/config.yml')

    # Configure pyglet
    pyglet.options['debug_gl'] = False

    # Create and run game
    window = Game(
        width=1280,
        height=720,
        caption='idle',
        resizable=True
    )

    pyglet.app.run()
