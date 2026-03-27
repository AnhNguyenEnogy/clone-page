---
description: Full release workflow — bump version, build Mac + Win, upload to SSH server + Google Drive, verify API
---

# Release Full (Mac + Win + Upload)

Workflow release hoàn chỉnh: bump version → build → publish upgrade → verify API → upload Google Drive.

// turbo-all

## 1. Bump Version

Tăng version ở 4 files:

| File             | Field                |
| ---------------- | -------------------- |
| `VERSION`        | Plain text version   |
| `app/version.py` | `__version__`        |
| `pyproject.toml` | `version`            |
| `CHANGELOG.md`   | Thêm entry mới ở đầu |

## 2. Configure SSH Once

Thiết lập theo `docs/ssh.md`. Workflow release dùng **SSH key / agent**, không dùng helper đăng nhập bằng secret plaintext.

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && ssh whisk-release 'hostname && docker --version'
```

Hoặc export env nếu không dùng host alias:

```bash
export WHISK_SSH_HOST=root@45.32.63.217
export WHISK_SSH_PORT=22
```

## 3. Build macOS

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && chmod +x scripts/build_mac.sh && ./scripts/build_mac.sh
```

## 4. Build Windows via Remote Docker + SSH

Windows release phải build trên server x86_64 vì Wine trong Docker trên Mac M-series không ổn định.

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && chmod +x scripts/release_remote_win.sh && ./scripts/release_remote_win.sh
```

Script này sẽ:

- sync source lên server qua `rsync + ssh`
- build portable `WhiskDesktop.exe` qua remote Docker
- build `x64_setup.exe` qua `amake/innosetup`
- kéo artifact về local `dist/v{VERSION}/win/`
- generate `SHA256SUMS.txt`, `version_info.txt`, `README.md`

## 5. Publish lên Server Upgrade Path

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && chmod +x scripts/publish_upgrade_release.sh && ./scripts/publish_upgrade_release.sh
```

Script publish sẽ:

- upload mọi file `.dmg` đang có trong `dist/v{VERSION}/mac/`
- upload `dist/v{VERSION}/win/x64_setup.exe`
- tự tạo và upload `x64_setup.exe.sha256` nếu còn thiếu
- verify file tồn tại trên server sau khi copy

## 6. Verify Auto-Update API

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && VERSION=$(cat VERSION) && PREV_VERSION=$(echo $VERSION | awk -F. '{printf "%d.%d.%d", $1, $2, $3-1}') && curl -s "https://tools.1nutnhan.com/auth/upgrade/check?tool=whisk&current_version=$PREV_VERSION&platform=mac" | python3 -m json.tool
```

Kiểm tra các field tối thiểu:

- `latest_version`
- `download_url`
- `file_name`
- `sha256` hoặc `checksum_url`

## 7. Upload lên Google Drive

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && VERSION=$(cat VERSION) && bash scripts/upload_release.sh "$VERSION"
```

---

## 8. Dọn Release Cũ (giữ lại 1 bản cũ)

> ⚠️ **Rule**: Luôn giữ lại **bản hiện tại + 1 bản trước đó** để rollback nếu bản mới có lỗi.

### 8a. Dọn local `dist/`

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && ls -d dist/v* 2>/dev/null | sort -V | head -n -2 | while read d; do echo "🗑️ Removing local: $d"; rm -rf "$d"; done && echo "✅ Local dist/ cleaned — kept latest 2 versions"
```

### 8b. Dọn SSH server `/root/mtips5s_match/upgrade/whisk/`

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && ssh "${WHISK_SSH_HOST:-whisk-release}" "cd /root/mtips5s_match/upgrade/whisk && ls -d v* 2>/dev/null | sort -V | head -n -2 | while read d; do echo \"🗑️ Removing server: \$d\"; rm -rf \"\$d\"; done && echo '✅ Server upgrade/ cleaned — kept latest 2 versions'"
```

### 8c. Dọn SSH server `/root/whisk_build/dist/`

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && ssh "${WHISK_SSH_HOST:-whisk-release}" "cd /root/whisk_build/dist && ls -d v* 2>/dev/null | sort -V | head -n -2 | while read d; do echo \"🗑️ Removing build cache: \$d\"; rm -rf \"\$d\"; done && echo '✅ Server build dist/ cleaned — kept latest 2 versions'"
```

### 8d. Dọn Google Drive

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && FOLDER_ID="${GDRIVE_FOLDER_ID:-1qH9dLTqP0qihAOD5r2QbU9SRpvk4v2hG}" && rclone lsd "gdrive:/" --drive-root-folder-id "$FOLDER_ID" 2>/dev/null | awk '{print $NF}' | sort -V | head -n -2 | while read d; do echo "🗑️ Removing Drive: $d"; rclone purge "gdrive:/$d" --drive-root-folder-id "$FOLDER_ID"; done && echo "✅ Google Drive cleaned — kept latest 2 versions"
```

## Notes

- **Docker Windows build** PHẢI chạy trên remote server (native x86_64) — Docker trên Mac M-series bị lỗi Wine ShellExecuteEx
- **SSH info**: `docs/ssh.md`
- **Google Drive**: cần `rclone` + remote `gdrive`, folder ID mặc định trong `scripts/upload_release.sh`
- **Server upgrade path**: `/root/mtips5s_match/upgrade/whisk/v{VERSION}/{mac,win}/`
- **Windows release rule**: chỉ phát hành `x64_setup.exe`; không upload `WhiskDesktop_v{VERSION}_win.zip`
- **Integrity rule**: publish `x64_setup.exe.sha256` cùng thư mục với installer
- **Cleanup rule**: Luôn giữ **2 bản mới nhất** (current + 1 prev) ở cả local, server, và Drive
