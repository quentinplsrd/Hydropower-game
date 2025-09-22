# HydropowerMarketGame.spec

# PyInstaller spec file for macOS .app build

# Imports

import sys
from PyInstaller.utils.hooks import collect\_all, collect\_dynamic\_libs
from PyInstaller.building.build\_main import Analysis, PYZ, EXE, COLLECT

# Collect ortools (Python + binaries + data)

ortools\_data, ortools\_binaries, ortools\_hiddenimports = collect\_all('ortools')

# Collect OpenCV binaries

cv2\_binaries = collect\_dynamic\_libs('cv2')

# Collect matplotlib backends

matplotlib\_hidden = \[
"matplotlib.backends.backend\_agg",
"matplotlib.backends.backend\_macosx",
]

a = Analysis(
\['HydropowerMarketGame.py'],
pathex=\[],
binaries=ortools\_binaries + cv2\_binaries,
datas=\[
('assets', 'assets'),  # bundle assets folder
] + ortools\_data,
hiddenimports=ortools\_hiddenimports + matplotlib\_hidden,
hookspath=\[],
hooksconfig={},
runtime\_hooks=\[],
excludes=\[],
win\_no\_prefer\_redirects=False,
win\_private\_assemblies=False,
cipher=None,
noarchive=False,
)

pyz = PYZ(a.pure, a.zipped\_data, cipher=a.cipher)

exe = EXE(
pyz,
a.scripts,
a.binaries,
a.zipfiles,
a.datas,
\[],
name='HydropowerMarketGame',
debug=False,
bootloader\_ignore\_signals=False,
strip=False,
upx=True,
console=False,  # equivalent to --noconsole / --windowed
icon='Game.icns',  # macOS will convert .ico to .icns if necessary
)

coll = COLLECT(
exe,
a.binaries,
a.zipfiles,
a.datas,
strip=False,
upx=True,
upx\_exclude=\[],
name='HydropowerMarketGame'
)
