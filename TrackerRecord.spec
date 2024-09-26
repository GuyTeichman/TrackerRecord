# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

datas = collect_data_files('tracker_record')
binaries = []
hiddenimports = []
hiddenimports += collect_submodules('numpy')
block_cipher = None

a = Analysis(
    ['tracker_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if is_darwin:
    exe_contents = (pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],)
    exe_kwargs = dict(runtime_tmpdir=None, icon='tracker_record/icon.icns')
else:
    splash = Splash('tracker_record/assets/splash.png',
                    binaries=a.binaries,
                    datas=a.datas,
                    text_pos=(175, 510),
                    text_font='Calibri',
                    text_size=16,
                    text_color='black',
                    always_on_top=False)
    exe_contents = (pyz, splash, a.scripts, [],)
    exe_kwargs = dict(exclude_binaries=True, icon='tracker_record/assets/icon.ico')

exe = EXE(
    *exe_contents,
    **exe_kwargs,
    name='TrackerRecord',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    hide_console='hide-late'
)

if not is_darwin:
    coll = COLLECT(
        exe,
        splash.binaries,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='TrackerRecord-1.0.0',
    )
