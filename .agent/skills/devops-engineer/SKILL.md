---
name: DevOps Engineer
description: Responsible for project setup, dependency management, cross-platform packaging (Mac .app + Windows .exe via PyInstaller), and CI/CD for the Whisk Desktop application.
---

# DevOps Engineer Skill

## Role Overview

The **DevOps Engineer** owns:

- Project initialization and dependency management
- Cross-platform packaging with **PyInstaller**
- Build scripts for macOS (`.app` bundle) and Windows (`.exe`)

---

## File Ownership

| File                        | Description                    |
| --------------------------- | ------------------------------ |
| `requirements.txt`          | Runtime + dev dependencies     |
| `build.spec`                | PyInstaller spec file          |
| `scripts/build_mac.sh`      | macOS build script             |
| `scripts/build_win.bat`     | Windows build script           |
| `scripts/release_remote_win.sh` | Remote Windows build via SSH + Docker |
| `scripts/publish_upgrade_release.sh` | Upload release artifacts lên server upgrade path qua SSH |
| `scripts/upload_release.sh` | Google Drive upload via rclone |

---

## Dependencies

### Runtime

```
PySide6>=6.6
```

### Development

```
pytest>=8.0
pytest-qt>=4.3
pytest-cov>=4.0
pyinstaller>=6.0
```

---

## PyInstaller Bundling

Resource files that must be included via `datas`:

- `app/theme/*.qss` — QSS stylesheets
- `app/theme/icons/*.svg` — SVG icons for spinbox arrows
- `app/i18n/*.json` — Translation files
- `app/assets/` — Logo and other assets

```python
datas=[
    ('app/theme/*.qss', 'app/theme'),
    ('app/theme/icons/*.svg', 'app/theme/icons'),
    ('app/i18n/*.json', 'app/i18n'),
    ('app/assets/*', 'app/assets'),
],
```

Use `resource_path()` in `app/utils.py` for all file loading:

```python
def resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)
```

---

## Build Commands

```bash
# macOS
chmod +x scripts/build_mac.sh && ./scripts/build_mac.sh

# Windows (from cmd or PowerShell)
scripts\build_win.bat

# Windows remote build via SSH server
chmod +x scripts/release_remote_win.sh && ./scripts/release_remote_win.sh
```

---

## Platform Notes

| Aspect       | macOS                   | Windows                              |
| ------------ | ----------------------- | ------------------------------------ |
| Python       | 3.9+                    | 3.9+                                 |
| Icon format  | `.icns`                 | `.ico`                               |
| Font default | SF Pro / Helvetica      | Segoe UI                             |
| Build output | `dist/WhiskDesktop.app` | `dist\WhiskDesktop\WhiskDesktop.exe` |

---

## Windows Installer (Inno Setup) — Critical Rules

> [!CAUTION]
> **KHÔNG BAO GIỜ** cài Inno Setup bên trong `tobix/pywine` Docker container — Wine trong container này không thể chạy Inno Setup installer (fail im lặng, không tạo file nào).

### Pipeline 2 bước bắt buộc:

| Bước | Docker Image | Nhiệm vụ |
|------|-------------|-----------|
| 1 | `tobix/pywine:3.11` | PyInstaller → `WhiskDesktop.exe` (portable) |
| 2 | `amake/innosetup:innosetup6` | ISCC → `x64_setup.exe` (installer) |

### Windows Release Rule:

- Windows release artifact chính thức chỉ là `x64_setup.exe`.
- Không upload hay phát hành `WhiskDesktop_v{VERSION}_win.zip` lên Google Drive.
- `WhiskDesktop/WhiskDesktop.exe` chỉ giữ làm artifact nội bộ để debug hoặc fallback cục bộ, không coi là release file cho user.

### Lệnh ISCC (bước 2):
```bash
docker run --rm --entrypoint bash \
  -v /root/whisk_build:/work:ro \
  -v /tmp/isout:/output \
  -w /work \
  amake/innosetup:innosetup6 \
  -c 'iscc /DMyAppVersion=$VERSION /O/output /work/scripts/installer.iss'
```

### Compression Rules:
- **`zip`** — dùng cho Docker builds (ổn định, không OOM)
- **`lzma` / `lzma2/ultra64`** — KHÔNG dùng trong Docker (OOM kill hoặc LZMA worker crash)
- **`lzma2/ultra64`** — chỉ dùng khi build trên Windows native (có Inno Setup cài sẵn)

### File Ownership:

| File | Mô tả |
|------|-------|
| `scripts/installer.iss` | Inno Setup script — tạo `x64_setup.exe` |
| `scripts/Dockerfile.win` | Docker image cho PyInstaller (bước 1) |
| `scripts/docker-compose.build.yml` | Compose file cho bước 1 (chỉ PyInstaller) |
| `scripts/update.bat` | Auto-update — ưu tiên `.exe` installer |

---

## SSH Release Rules

- SSH release workflow phải dùng **SSH key / agent / `~/.ssh/config`**, không nhúng password trong docs hoặc script.
- `docs/ssh.md` chỉ được chứa host/config mẫu, **không chứa secret**.
- Release Windows qua server phải đi theo 2 pha:
  1. `scripts/release_remote_win.sh` — sync source, build portable + `x64_setup.exe`, kéo artifact về local `dist/v{VERSION}/win/`
  2. `scripts/publish_upgrade_release.sh` — upload artifact lên server upgrade path
- Upload Google Drive là bước riêng qua `scripts/upload_release.sh`; không thay thế server upgrade path.
- Với Windows release, upload cả `x64_setup.exe` và sibling checksum `x64_setup.exe.sha256` để hỗ trợ integrity metadata cho updater.
