"""ClipMint Windows adaptation of the Crimson/Kohaku gothic workstation palette."""
CSS = r'''
QMainWindow, QWidget#root { background:#130e16; color:#f5e3d9; }
QWidget { font-family:Georgia; font-size:12px; color:#f3e4d9; }
QLabel#brand { font:italic 39px Georgia; color:#efd0a1; }
QLabel#japanese { color:#dfaeb0; font-family:'Yu Gothic'; font-size:12px; }
QLabel#micro { color:#d8969d; font-family:Consolas; font-size:10px; }
QFrame#panel { background:#22151f; border:1px solid #80505b; border-radius:8px; }
QLabel#section { font:italic 25px Georgia; color:#f3decd; }
QLabel#subhead { font:11px Consolas; color:#d78997; }
QLineEdit, QComboBox { background:#2a1d29; border:1px solid #885562; border-radius:6px; padding:9px; color:#f2e6df; font:12px Consolas; }
QLineEdit:focus { border:1px solid #e4aa84; }
QListWidget { background:#1b121c; border:1px solid #68404d; border-radius:6px; font:13px Georgia; outline:0; }
QListWidget::item { padding:10px 8px; border-bottom:1px solid #51313e; }
QListWidget::item:selected { background:#633244; border-left:3px solid #ff7c9c; color:#ffe8dc; }
QPushButton { background:#4b2738; border:1px solid #9a6276; border-radius:5px; padding:9px 12px; color:#f6e7db; }
QPushButton:hover { background:#753b53; }
QPushButton:disabled { background:#251b26; color:#877c83; }
QPushButton#primary { background:#9f294c; border-color:#e58a9e; font:italic 17px Georgia; }
QPushButton#light { background:#ecdcd7; color:#38202b; border-color:#efd4ce; }
QPushButton#module { text-align:left; padding:14px 9px; background:#281a27; }
QPushButton#module:checked { background:#653145; border-left:3px solid #ff829b; }
QLabel#status { font:10px Consolas; color:#cbea91; }
QLabel#preview { background:#130f17; border:1px solid #6a485b; border-radius:6px; }
QScrollBar:vertical { background:#261a27; width:10px; }
QScrollBar::handle:vertical { background:#96536f; border-radius:5px; }
'''
