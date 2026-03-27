---
description: Build macOS DMG using PyInstaller, upload to server, and verify auto-update API
---

# Build & Release macOS App

## Prerequisites

- PyInstaller ≥ 6.0 (`pip install pyinstaller`)
- `VERSION` file ở root project chứa version string (ví dụ `1.0.0`)
- SSH key / agent đã cấu hình theo `docs/ssh.md`

## Version Bump

Khi release, **PHẢI bump version** ở tất cả 4 files:

| File             | Field                |
| ---------------- | -------------------- |
| `VERSION`        | Plain text version   |
| `app/version.py` | `__version__`        |
| `pyproject.toml` | `version`            |
| `CHANGELOG.md`   | Thêm entry mới ở đầu |

## Steps

// turbo-all

1. **Build macOS package**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && chmod +x scripts/build_mac.sh && ./scripts/build_mac.sh
```

2. **Publish DMG lên upgrade path**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && chmod +x scripts/publish_upgrade_release.sh && ./scripts/publish_upgrade_release.sh
```

3. **Verify auto-update API**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && VERSION=$(cat VERSION) && PREV_VERSION=$(echo $VERSION | awk -F. '{printf "%d.%d.%d", $1, $2, $3-1}') && curl -s "https://tools.1nutnhan.com/auth/upgrade/check?tool=whisk&current_version=$PREV_VERSION&platform=mac" | python3 -m json.tool
```

4. **Upload lên Google Drive (optional)**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && VERSION=$(cat VERSION) && bash scripts/upload_release.sh "$VERSION"
```

## Output

```
dist/
└── v{VERSION}/
    └── mac/
        ├── WhiskDesktop.dmg
        ├── version_info.txt
        └── README.md
```

Server:

```
/root/mtips5s_match/upgrade/whisk/v{VERSION}/mac/
└── WhiskDesktop.dmg
```

Google Drive (`gdrive:/v{VERSION}/`):

```
v{VERSION}/
├── WhiskDesktop_v{VERSION}_mac.zip
└── WhiskDesktop_v{VERSION}_extension.zip
```
