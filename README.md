# sora-secretary

## ローカル運用

- SORA 上で `sora-secretary-api.service` (user systemd) として常駐
- Mint 側でビルドした `aster-ui/dist` を FastAPI が静的配信
- SORA には node/npm を入れず、ビルドは Mint 側で行う
- Memory UI の表示、restart、status 確認は Mint 側の launcher から操作
- deploy / systemd / DB / secret の操作は行わない
