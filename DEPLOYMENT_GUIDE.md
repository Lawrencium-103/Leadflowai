# 🚀 LeadFlow AI - Deployment Guide

## Deploying to Streamlit Cloud

### Step 1: Prepare Your Repository

1. **Push to GitHub** (Already done! ✅)
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select:
   - **Repository**: `Lawrencium-103/Leadflowai`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **"Deploy"**

### Step 3: Configure API Keys (CRITICAL!)

After deployment, you need to add your API keys as **Streamlit Secrets**:

1. In your deployed app dashboard, click **"⚙️ Settings"**
2. Go to **"Secrets"** section
3. Add the following in TOML format:

```toml
TAVILY_API_KEY = "tvly-xxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENROUTER_API_KEY = "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx"
```

4. Click **"Save"**
5. Your app will automatically restart with the secrets loaded

---

## Getting Your API Keys

### 🔍 Tavily API Key

1. Go to [tavily.com](https://tavily.com)
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API key
5. **Free tier**: 1,000 searches/month

### 🤖 OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up and verify your email
3. Go to **"Keys"** section
4. Create a new API key
5. Add credits to your account (pay-as-you-go)

---

## Local Development Setup

For testing locally before deployment:

1. **Create `.streamlit/secrets.toml`** (already created):
   ```bash
   cd "c:\Users\user\Desktop\AI Agent Project\LeadFlow"
   ```

2. **Edit `.streamlit/secrets.toml`** and add your keys:
   ```toml
   TAVILY_API_KEY = "your-actual-tavily-key"
   OPENROUTER_API_KEY = "your-actual-openrouter-key"
   ```

3. **Run locally**:
   ```bash
   streamlit run app.py
   ```

> **Note**: The `secrets.toml` file is already in `.gitignore`, so it won't be pushed to GitHub.

---

## Alternative: Environment Variables

If you prefer using environment variables instead:

### Windows (PowerShell):
```powershell
$env:TAVILY_API_KEY="your-key-here"
$env:OPENROUTER_API_KEY="your-key-here"
streamlit run app.py
```

### Linux/Mac:
```bash
export TAVILY_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"
streamlit run app.py
```

---

## Priority Order for API Keys

The app checks for API keys in this order:

1. **Streamlit Secrets** (`.streamlit/secrets.toml` locally, or Streamlit Cloud secrets)
2. **Environment Variables** (`TAVILY_API_KEY`, `OPENROUTER_API_KEY`)
3. **Manual Input** (via the sidebar in the app)

---

## Troubleshooting

### "API Keys missing" Error

**Solution**: Make sure you've added the keys to Streamlit Secrets (for cloud) or `secrets.toml` (for local).

### Tavily Search Fails

**Possible causes**:
- Invalid API key
- Rate limit exceeded (free tier: 1,000/month)
- Network issues

**Fallback**: The app uses DuckDuckGo and RSS feeds as backup search methods.

### Gmail Authentication Issues

See the in-app guide under **"🛠️ How to fix this (Gmail Setup Guide)"** in the app itself.

---

## Security Best Practices

✅ **DO**:
- Use Streamlit Secrets for deployment
- Keep `secrets.toml` in `.gitignore`
- Rotate API keys periodically

❌ **DON'T**:
- Commit API keys to GitHub
- Share your `secrets.toml` file
- Hardcode keys in the source code

---

## Support

For issues or questions:
- **Email**: oladeji.lawrence@gmail.com
- **Phone**: +234 903 881 9790

---

**Your app is now ready for deployment! 🎉**
