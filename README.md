# rainAlert

雨が降りそうになったらメールで通知してくれる Python スクリプト。
GitHub Actions で定期実行するため、PC の電源が切れていても動作します。

## GitHub Actions でのセットアップ

### 1. GitHub にリポジトリを作成してプッシュ

```bash
cd ~/rainAlert
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/あなたのユーザー名/rainAlert.git
git push -u origin master
```

### 2. GitHub Secrets に設定を登録

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を登録:

**場所:**

| Secret 名 | 値の例 |
|---|---|
| `RAIN_LOCATION_NAME` | 東京 |
| `RAIN_LOCATION_LAT` | 35.6895 |
| `RAIN_LOCATION_LON` | 139.6917 |

**メール:**

| Secret 名 | 値 |
|---|---|
| `RAIN_EMAIL_SENDER` | 送信元 Gmail アドレス |
| `RAIN_EMAIL_PASSWORD` | Gmail アプリパスワード (16文字) |
| `RAIN_EMAIL_RECIPIENT` | 受信先メールアドレス |

**Gmail アプリパスワードの取得:**
1. Google アカウント → セキュリティ → 2段階認証を有効化
2. セキュリティ → アプリパスワード → 新規生成 (16文字)

### 3. 動作確認（手動実行）

GitHub リポジトリの **Actions タブ → Rain Alert → Run workflow** から手動実行できます。

---

## ローカルでのテスト

`config.yaml` のコメントを外して場所・メール設定を入力:

```yaml
location:
  name: "東京"
  latitude: 35.6895
  longitude: 139.6917

email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender: "your@gmail.com"
  password: "your_app_password"
  recipient: "your@gmail.com"
```

```bash
pip3 install -r requirements.txt

# メールを送らずにテスト
python3 main.py --dry-run

# クールダウン無視してメール送信テスト
python3 main.py --force
```

---

## ファイル構成

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント。フロー制御・クールダウン管理 |
| `weather.py` | Open-Meteo API から降水確率を取得 |
| `notifier.py` | SMTP でメール送信 |
| `config.yaml` | アラート閾値のみ（場所・メール情報は Secrets で管理） |
| `state.json` | 前回通知時刻（自動生成・gitignore済み） |
| `.github/workflows/rain_alert.yml` | GitHub Actions スケジュール設定 |

## 設定パラメータ (`config.yaml`)

| キー | 値 | 説明 |
|---|---|---|
| `rain_probability_threshold` | 50 | 通知する降水確率の閾値 (%) |
| `check_hours_ahead` | 1 | 今後何時間先まで確認するか |
| `cooldown_hours` | 6 | 連続通知を防ぐ最小間隔 (時間) |
