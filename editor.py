import pyglet
from pyglet.window import Window, key, mouse
from editor.editor_window import EditorWindow

def main():
    """Launch the tech tree editor."""
    window = EditorWindow(
        width=900,
        height=900,
        caption="Tech Tree Editor",
        resizable=True
    )
    pyglet.app.run()


if __name__ == '__main__':
    main()
