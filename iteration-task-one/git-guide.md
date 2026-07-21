# Git 操作指引（分支与同步）

适用场景：当前远程仓库只有一个 master 分支，需要在本地创建/切换分支，并在提交、推送前同步远程更新。

## 基本约定
- 保持 master 分支干净，仅用于同步远程和创建新分支。
- 新分支命名示例：`feature/<任务名>`、`fix/<问题描述>`。
- 推荐使用 rebase 方式保持提交历史整洁。

## 创建新分支
1) 确保在 master 且最新：
```bash
git checkout master
git fetch origin master
git pull --rebase origin master
```
2) 创建并切换到新分支：
```bash
git checkout -b feature/<任务名>
```

## 切换分支
- 切换到已有分支：
```bash
git checkout <分支名>
```
- 返回 master：
```bash
git checkout master
```
- 若有未提交改动，先 `git status`，必要时使用 `git stash push -m "临时保存"` 再切换，切换后可 `git stash pop` 取回。

## 在开发分支同步远程更新（提交前务必执行）
1) 获取远程最新 master：
```bash
git fetch origin master
```
2) 保持当前分支（如 feature/...），将 master 更新 rebase 进来：
```bash
git rebase origin/master
```
3) 若 rebase 产生冲突，按文件解决后：
```bash
git add <解决冲突的文件>
git rebase --continue
```

## 提交与推送
1) 提交前检查：
```bash
git status
```
2) 提交更改：
```bash
git add <文件或目录>
git commit -m "描述本次改动"
```
3) 再次确认已与远程同步（如有必要，可重复 rebase 步骤）。
4) 首次推送分支到远程：
```bash
git push -u origin <分支名>
```
之后同一分支可直接 `git push`。

## 从 master 同步最新代码再继续开发（可选快速路径）
- 在任意分支执行：
```bash
git fetch origin master
git rebase origin/master
```
- 若仅想查看差异，可使用：
```bash
git diff origin/master
```

## 常见问题
- 如果误在 master 上开发：
  - 创建新分支并移动提交：
  ```bash
  git checkout -b feature/<任务名>
  ```
  - 回到 master，重置到远程：
  ```bash
  git checkout master
  git reset --hard origin/master
  ```
- 如果推送被拒绝（远程有新提交）：先 `git fetch origin master`，在当前分支 `git rebase origin/master`，解决冲突后再 `git push -f`（谨慎使用，确认仅自己在该分支工作）。
