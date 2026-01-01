90% vibes

## Requirements

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tech-tree-editor.git
cd tech-tree-editor
```

### 2. Create Virtual Environment

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt when the virtual environment is active.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:

```bash
pip install pyglet pyyaml
```

### 4. Run the Application

```bash
python main.py
```

Or if you have an `editor_window.py` as the entry point:

```bash
python editor_window.py
```

## Project Structure

```
tech-tree-editor/
├── data/                      # Tech tree YAML files
│   ├── tech_tree_actions.yml
│   ├── tech_tree_soc.yml
│   └── tech_tree_tech.yml
├── editor/                    # Editor UI components
│   ├── editor_canvas.py      # Canvas for node visualization
│   ├── editor_properties.py  # Properties panel
│   ├── editor_sidebar.py     # Sidebar with tools
│   └── editor_window.py      # Main editor window
├── loader.py                  # Data models and YAML loader
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Usage

### Basic Controls

#### Mouse:
- **Left-click + drag** - Move nodes
- **Right-click + drag** - Pan canvas
- **Scroll wheel** - Zoom in/out
- **Left-click node** - Select node
- **Left-click empty space** - Deselect

#### Keyboard Shortcuts:
- **C** - Start connection mode (connect selected node to another)
- **Del / Backspace** - Delete selected node
- **L** - Auto-layout tree
- **R** - Reset camera position
- **Ctrl+S** - Save current tree
- **Ctrl+N** - Create new tree
- **ESC** - Cancel operation / Deselect
- **ESC (double-tap)** - Quit application

### Creating a Tech Tree

1. **Create a New Tree:**
   - Click "📄 New Tree" in the sidebar
   - Or press `Ctrl+N`

2. **Add Nodes:**
   - Click "➕ Add Node" button
   - A new upgrade node will appear in the center

3. **Edit Node Properties:**
   - Click on a node to select it
   - Edit properties in the right panel:
     - Name, Description
     - Tier, Year
     - Exclusive Group
     - Effects (resource modifications)
     - Costs (resource requirements)

4. **Create Dependencies:**
   - Select a node
   - Press `C` to enter connection mode
   - Click on the target node to create a dependency
   - Press `ESC` to cancel

5. **Organize Layout:**
   - Manually drag nodes to position them
   - Or press `L` for automatic layout based on tiers

6. **Save Your Work:**
   - Click "💾 Save Tree"
   - Or press `Ctrl+S`
   - Files are saved to the `data/` folder

### Loading Existing Trees

- Click on any tree file in the sidebar's "Load Tree" section
- Or click "📂 Load Tree" and enter a file path
- The first tree file is auto-loaded on startup


## Troubleshooting

### Virtual Environment Issues

**Problem:** `venv\Scripts\activate` not found (Windows)
```bash
# Try using:
venv\Scripts\activate.bat
# Or:
venv\Scripts\Activate.ps1  # PowerShell
```

**Problem:** Permission denied (macOS/Linux)
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Dependency Issues

**Problem:** `ModuleNotFoundError: No module named 'pyglet'`
```bash
# Make sure virtual environment is activated
pip install pyglet pyyaml
```

**Problem:** Pyglet window doesn't open
```bash
# Install system dependencies (Linux):
sudo apt-get install python3-opengl
```

### Application Issues

**Problem:** No tree files appear in sidebar
- Ensure `data/` folder exists
- Check that YAML files contain "tree" in the filename
- Verify YAML files are properly formatted

**Problem:** Can't edit text fields
- Click directly on the text field (not the label)
- Look for the blue border indicating active field
- Press ESC to exit editing mode if stuck

## Deactivating Virtual Environment

When you're done working:

```bash
deactivate
```


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Credits

- Built with [Pyglet](https://pyglet.org/) - Python OpenGL framework
- YAML parsing with [PyYAML](https://pyyaml.org/)

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
