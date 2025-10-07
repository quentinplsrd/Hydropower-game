# -*- mode: python ; coding: utf-8 -*-

datas = [('assets', 'assets')]
binaries = []

# Removed ortools - only keep matplotlib backend
hiddenimports = ['matplotlib.backends.backend_agg']

a = Analysis(
    ['HydropowerMarketGame.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'unittest', '_tkinter'],  # Exclude unused modules
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Changed to onedir mode for faster startup
    name='HydropowerMarketGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Enable stripping to reduce size
    upx=False,  # Disable UPX on macOS (causes delays)
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name='HydropowerMarketGame'
)

app = BUNDLE(
    coll,
    name='HydropowerMarketGame.app',
    icon='Game.icns',
    bundle_identifier=None,
    bundle_name='Hydropower Game'
)
