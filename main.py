import pyglet
from game import Game

if __name__ == '__main__':
    # Configure pyglet
    pyglet.options['debug_gl'] = False
    
    # Create and run game
    window = Game(
        width=1280,
        height=720,
        caption='Tech Tree Game',
        resizable=True
    )
    
    pyglet.app.run()

