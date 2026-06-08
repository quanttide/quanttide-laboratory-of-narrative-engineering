## Git Push 规范

每次提交后必须推送到远程仓库。

```sh
# 1. 推送主仓库
git push

# 2. 推送有更新的子模块（处理 detached HEAD）
#    只推送 HEAD 有变更的子模块，如果子模块不在 main 分支则跳过
git submodule foreach '
  if git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -q main; then
    git push origin HEAD:main
  fi
'
```

> 如果某个子模块在 detached HEAD 上且有新提交，先 `cd` 到该子模块内，切到 main 分支再 push。
