# GitHub 正确工作流指南

## 前提

- 安装 [GitHub CLI](https://cli.github.com/)（`winget install GitHub.cli`）
- 登录：`gh auth login`
- 如果走代理：`set HTTPS_PROXY=http://127.0.0.1:7890`

## 标准流程（5 步）

### 1. Fork 上游仓库

在 GitHub 网页上点击 **Fork** 按钮，或者命令行：

```bash
gh repo fork https://github.com/原作者的仓库.git --clone=false
```

这会在你的账户下创建一个关联上游的副本。

### 2. Clone 自己的 Fork

```bash
git clone https://github.com/你的用户名/仓库.git
cd 仓库
```

### 3. 添加上游远程

```bash
git remote add upstream https://github.com/原作者的仓库.git
```

验证：

```bash
git remote -v
# origin    https://github.com/你的用户名/仓库.git (fetch/push)  ← 你自己的
# upstream  https://github.com/原作者的仓库.git (fetch/push)     ← 原作者的
```

### 4. 修改代码并提交

```bash
git add -A
git commit -m "feat: 描述你的改动"
```

### 5. 推送到自己的 Fork

```bash
git push origin main
```

**注意：永远不要 `--force` push。**

---

## 同步上游更新

当原作者更新了代码，拉到本地：

```bash
git pull upstream main
git push origin main
```

---

## 提 Pull Request（可选）

在 GitHub 网页上你自己的 fork 页面，点 **Contribute** → **Open Pull Request**，你的代码就能合并到上游。

---

## 常见错误

| 错误做法 | 正确做法 |
|---------|---------|
| 下载 ZIP 改完 `git init` + `force push` | Fork → Clone → 改 → Commit → Push |
| `git push --force` | `git push` |
| 不设 upstream remote | `git remote add upstream ...` |
| 不提交 PR，直接发文件 | 提 Pull Request |

---

## 远程关系图

```
YorickFin/AutoGame (上游)
       ↑ fork
icmkh1/AutoGame (你的 fork)  ← origin
       ↑ clone
    本地代码  → 修改 → commit → push → origin
       ↓
    Pull Request → upstream (可选)
```
