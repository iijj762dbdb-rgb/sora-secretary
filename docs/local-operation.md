# Local Operation Notes

SORA Secretary は SORA 上で user systemd service として常駐します。
UI (aster-ui) の build は開発マシン (Mint) 側で行い、生成された dist を SORA へ rsync/scp で配置します。
SORA には node / npm を導入しません。build 環境は Mint 側にのみ存在します。

## 役割分担

| 項目 | 開発マシン (Mint) | SORA (実行環境) |
| :--- | :--- | :--- |
| コード編集・テスト | ✅ | — |
| UI build (`npm run build`) | ✅ | — |
| node / npm | ✅ (build 時のみ) | — |
| Bot 常駐 (systemd user service) | — | ✅ |
| 秘密情報・DB 保持 | — | ✅ |

## dist 配置

```bash
# Mint 側で build
cd aster-ui
npm run build

# SORA へ配置
rsync -avz --delete dist/ sora:/home/okota/code/sora-secretary/aster-ui/dist/
```
