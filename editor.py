# editor.py
import pyglet
from pyglet.window import Window, key, mouse
from ui.editor_window import EditorWindow


def main():
    """Launch the tech tree editor."""
    window = EditorWindow(
        width=1400,
        height=900,
        caption="Tech Tree Editor",
        resizable=True
    )

    pyglet.app.run()


if __name__ == '__main__':
    main()
