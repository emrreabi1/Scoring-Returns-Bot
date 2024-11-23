# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['executable.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/leagues_available.json', 'assets'),
        ('assets/images/*.png', 'assets/images'),
        ('configs', 'configs'),
        ('scripts', 'scripts'),
        ('bot', 'bot'),
    ],
    hiddenimports=[
        'PyQt6',
        'asyncio',
        'json',
        'logging',
        'pathlib',
        'pandas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ScoringReturnsBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/images/Logo_Oficial.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
