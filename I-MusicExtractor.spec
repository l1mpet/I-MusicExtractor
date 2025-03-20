# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['I-MusicExtractor-GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('music_icon.png', '.'), ('I-MusicExtractor.py', '.'), ('I-MusicExtractor-GUI.py', '.')],
    hiddenimports=['PIL', 'PIL._tkinter_finder', 'mutagen', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='I-MusicExtractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='music_icon.icns',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='I-MusicExtractor',
)
app = BUNDLE(
    coll,
    name='I-MusicExtractor.app',
    icon='music_icon.icns',
    bundle_identifier='com.imusicextractor.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSUIElement': '0',
        'CFBundleName': 'I-MusicExtractor',
        'CFBundleDisplayName': 'I-MusicExtractor',
        'CFBundleGetInfoString': 'Music Extraction and Organization Tool',
    },
) 