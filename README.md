# 📧 Gmail to Discord
**An open-source tool that automatically categorizes and forwards Gmail messages to Discord channels based on keywords.**

<br/>

### ✨ Features
- 🔍 **Keyword-based Filtering**: Automatically categorize emails based on subject and sender <br/>
- 📊 **Multi-channel Support**: Send to multiple channels if email matches multiple keywords <br/>
- 🎨 **Color Coding**: Visual distinction with different colors per category <br/>
- 🤖 **Automated**: Runs automatically at customizable intervals via GitHub Actions <br/>

### 📋 Prerequisites

- GitHub account
- Google account (Gmail)
- Discord server admin permissions

---

<br/>

### 🚀 Setup Instructions

#### Step 1: Fork the Repository

#### Step 2: Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to **APIs & Services** → **Library**
4. Search for "Gmail API" and **Enable** it
5. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
6. Application type: **Desktop app**
7. Download `credentials.json`

<br/>

#### Step 3: Create Discord Webhooks 

Create a webhook for each Discord channel:

1. Right-click on Discord channel
2. **Edit Channel** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. **Copy Webhook URL** (save for later)

Example channel setup:
- `#payments` - Payment-related emails
- `#shipping` - Delivery tracking
- `#newsletters` - Subscription newsletters
- `#misc` - Uncategorized emails

<br/>

#### Step 4: Configure Settings

1. Clone your forked repository locally:

2. Copy `config.example.json` to `config.json`:
```bash
cp config.example.json config.json
```

3. Edit `config.json`:
```json
{
  "keywords": [
    {
      "keywords": ["payment", "paid", "invoice"],
      "webhook": "YOUR_DISCORD_WEBHOOK_URL_1",
      "color": "green"
    },
    {
      "keywords": ["shipping", "delivery"],
      "webhook": "YOUR_DISCORD_WEBHOOK_URL_2",
      "color": "blue"
    }
  ],
  "default_webhook": "YOUR_DEFAULT_WEBHOOK_URL",
  "default_color": "default"
}
```

**Available colors:**
- `red`, `green`, `blue`, `yellow`, `purple`, `orange`, `pink`, `teal`, `default`
- Or hex color codes (e.g., `#DE5733`)

<br/>

#### Step 5: Gmail Authentication

1. Set up Python environment:
```bash
pip install -r requirements.txt
```

2. Run locally once:
```bash
python gmail_discord_sync.py
```

3. Browser will open - log in with your Google account
4. Grant permissions
5. `token.json` file will be created

<br/>

#### Step 6: Configure GitHub Secrets

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `GMAIL_CREDENTIALS`
4. Value: Copy and paste entire contents of `token.json`

<br/>

#### Step 7: Upload config.json

**⚠️ Warning**: Never upload `credentials.json` or `token.json` to GitHub!
(Already included in `.gitignore`)

---

<br/>

### ⚙️ Changing Run Frequency

Edit the cron value in `.github/workflows/sync.yml`:

```yaml
schedule:
  # Every 15 minutes (default)
  - cron: '*/15 * * * *'
  
  # Every hour
  - cron: '0 * * * *'
  
  # Every 30 minutes, weekdays 9 AM - 6 PM
  - cron: '*/30 9-18 * * 1-5'
```

### 🔍 Verify Operation

1. Go to your GitHub repository → **Actions** tab
2. Check "Gmail to Discord Sync" workflow
3. Use **Run workflow** button for manual execution
4. Check logs for execution results

### 📊 Keyword Matching

- **Partial matching**: Setting "payment" matches "payment complete", "payment history", etc.
- **Case insensitive**: "Payment" and "payment" are treated the same
- **Multiple channels**: Email with multiple keywords sends to all matching channels
- **Sender email**: Keywords also match against sender email address

### 💡 Usage Examples

#### E-commerce Notifications
```json
{
  "keywords": [
    {
      "keywords": ["order", "payment", "purchase"],
      "webhook": "...",
      "color": "green"
    },
    {
      "keywords": ["shipping", "shipped"],
      "webhook": "...",
      "color": "blue"
    },
    {
      "keywords": ["shop@", "store@", "amazon"],
      "webhook": "...",
      "color": "purple"
    }
  ]
}
```

#### Work Email Classification
```json
{
  "keywords": [
    {
      "keywords": ["urgent", "asap", "critical"],
      "webhook": "...",
      "color": "red"
    },
    {
      "keywords": ["meeting", "calendar"],
      "webhook": "...",
      "color": "blue"
    },
    {
      "keywords": ["@company.com"],
      "webhook": "...",
      "color": "green"
    }
  ]
}
```

---

<br/>

### 🔧 Troubleshooting

#### Q: GitHub Actions not running
A: 
- Verify `GMAIL_CREDENTIALS` Secret is set correctly
- Check if workflow is enabled in Actions tab
- Check repository Settings → Actions → General → Workflow permissions

#### Q: No messages in Discord
A:
- Verify Webhook URL is correct
- Check Discord channel permissions
- Check error messages in Actions logs

### 📝 License

MIT License - Free to use, modify, and distribute.

### 🤝 Contributing

Bug reports, feature suggestions, and Pull Requests are all welcome :)
