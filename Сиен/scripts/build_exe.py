# Файл: scripts/build_exe.py
"""
Сборка лаунчера в .exe через PyInstaller
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build():
    """Собрать .exe файл"""
    
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['{os.path.join(BASE_DIR, "sien_launcher.py")}'],
    pathsep=['{BASE_DIR}'],
    binaries=[],
    datas=[
        ('{os.path.join(BASE_DIR, "web")}', 'web'),
        ('{os.path.join(BASE_DIR, "hud")}', 'hud'),
    ],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'aiohttp',
        'psutil',
        'cryptography',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={{}},
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
    name='Sien',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{os.path.join(BASE_DIR, "icon.ico")}' if os.path.exists('{os.path.join(BASE_DIR, "icon.ico")}') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sien',
)
'''
    
    spec_path = os.path.join(BASE_DIR, "sien.spec")
    
    with open(spec_path, "w") as f:
        f.write(spec_content)
    
    print("Building Sien executable...")
    print(f"Spec file: {spec_path}")
    
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        spec_path
    ])
    
    print("\nBuild complete!")
    print(f"Executable location: {os.path.join(BASE_DIR, 'dist', 'Sien')}")


if __name__ == "__main__":
    build()
