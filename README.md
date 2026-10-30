# 1030Software-engineering
# 活動報名系統

軟體工程 小組作業

## 組員分工

| 組員 | 負責功能 |
|---|---|
| 組員A | F1 新增活動、資料庫 |
| 組員B | F2 活動清單、F3 報名表 |
| 組員C | F4 送出報名、F5 報名清單 |

詳細需求見 [requirements.md](requirements.md)，資料表見 [schema.sql](schema.sql)。

## 系統流程

1. 管理者新增活動
2. 使用者在活動清單選擇活動，點「報名」
3. 填寫姓名、電話，送出完成報名
4. 管理者查看該活動的報名清單

## 協作流程

1. 開始前先 `git pull` 取得最新版本
2. 開自己的分支：`git switch -c feature/功能名稱`
3. 完成後 commit 並 push，到 GitHub 開 Pull Request
4. 組員確認後 merge 進 main