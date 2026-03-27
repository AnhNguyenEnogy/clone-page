# Build Rules

## Targets

Chỉ build **2 target** duy nhất:

| Target      | Output                                                               | Cách build                               |
| ----------- | -------------------------------------------------------------------- | ---------------------------------------- |
| **Windows** | `dist-win/WhiskDesktop.exe`                                          | Docker (PyInstaller on Wine)             |
| **macOS**   | `dist/WhiskDesktop-AppleSilicon.dmg` + `dist/WhiskDesktop-Intel.dmg` | PyInstaller (arm64 + x86_64 via Rosetta) |

## Python 3.9 Compatibility (CRITICAL)

Bản Intel dùng Python 3.9 (system Python qua Rosetta). Mọi file Python **phải có**:

```python
from __future__ import annotations
```

ở đầu file (sau docstring) để tránh lỗi `TypeError: unsupported operand type(s) for |`.

## SSL Certificates (CRITICAL)

PyInstaller-bundled apps **không tìm được system CA certs**.

**Bắt buộc:**

1. `certifi` trong `requirements.txt`, `Dockerfile.win`, và `build.spec` → `hiddenimports`
2. `scripts/runtime_hook.py` set `SSL_CERT_FILE` từ certifi

## Windows Build

```bash
docker build --platform linux/amd64 -f scripts/Dockerfile.win -t whisk-win . && \
docker create --name whisk-tmp whisk-win && \
docker cp whisk-tmp:/src/dist/WhiskDesktop ./dist-win && \
docker rm whisk-tmp
```

## macOS Build

Chạy workflow `/build-app` — tự động build cả 2 kiến trúc + đóng gói DMG.

**Nội dung mỗi DMG:**

- `WhiskDesktop.app` (ad-hoc signed)
- `run_whisk.command` — terminal launcher xem log
- `HUONG_DAN_CAI_DAT.txt` — hướng dẫn cài đặt tiếng Việt
- Shortcut `Applications`

**Lưu ý:**

- App chưa notarize → khách phải Right-click → Open lần đầu
- Crash logs: `~/Downloads/Whisk_pro/logs/crash.log`
