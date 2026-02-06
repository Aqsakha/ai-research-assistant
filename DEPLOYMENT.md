# Deployment Guide - CerebroGPT

This guide covers deploying CerebroGPT to the cloud using **Render** (backend) and **Vercel** (frontend).

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│     Vercel      │  HTTP   │     Render      │
│   (Frontend)    │ ──────► │   (Backend)     │
│   Angular App   │         │   Flask API     │
└─────────────────┘         └─────────────────┘
```

---

## Step 1: Deploy Backend to Render

### Option A: Deploy via Render Dashboard

1. Go to [render.com](https://render.com) and sign up/log in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `cerebrogpt-api`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

5. Add Environment Variables:
   - `GOOGLE_API_KEY` = your Google AI API key
   - `SERPAPI_API_KEY` = your SerpAPI key
   - `FLASK_ENV` = `production`

6. Click **"Create Web Service"**

### Option B: Deploy via render.yaml (Blueprint)

1. Push the code to GitHub
2. Go to Render Dashboard → **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will detect `render.yaml` and configure automatically
5. Add the environment variables when prompted

### Get Your Backend URL

After deployment, Render will provide a URL like:
```
https://cerebrogpt-api.onrender.com
```

**Save this URL** - you'll need it for the frontend.

---

## Step 2: Deploy Frontend to Vercel

### Option A: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign up/log in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Angular
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build -- --configuration production`
   - **Output Directory**: `dist/ai-research-assistant-frontend`

5. Add Environment Variable (optional, for build-time replacement):
   - Click **"Environment Variables"**
   - This project uses hardcoded URL in `environment.prod.ts`

6. Click **"Deploy"**

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Deploy
vercel

# Follow the prompts to link your project
```

---

## Step 3: Configure Frontend Backend URL

**Before deploying the frontend**, update the backend URL:

Edit `frontend/src/environments/environment.prod.ts`:

```typescript
export const environment = {
  production: true,
  backendUrl: 'https://cerebrogpt-api.onrender.com'  // Your Render URL
};
```

Then redeploy the frontend:
```bash
cd frontend
vercel --prod
```

Or push to GitHub and Vercel will auto-deploy.

---

## Environment Variables Summary

### Backend (Render)

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI/Gemini API key | Yes |
| `SERPAPI_API_KEY` | SerpAPI key for web search | Yes |
| `FLASK_ENV` | Set to `production` | Recommended |

### Frontend (Vercel)

The frontend uses build-time configuration. Update `environment.prod.ts` with your backend URL before deploying.

---

## Verify Deployment

### Test Backend

```bash
# Health check
curl https://cerebrogpt-api.onrender.com/health

# Test research endpoint
curl "https://cerebrogpt-api.onrender.com/research?query=test"
```

### Test Frontend

Visit your Vercel URL (e.g., `https://cerebrogpt.vercel.app`) and try a research query.

---

## Troubleshooting

### CORS Issues

The backend is configured to allow all origins. If you encounter CORS issues:

1. Check that `Flask-CORS` is installed
2. Verify the backend URL in `environment.prod.ts` is correct
3. Ensure no trailing slash in the URL

### Backend Not Responding

1. Check Render logs for errors
2. Verify environment variables are set
3. Test the `/health` endpoint directly

### Frontend Build Fails

1. Ensure Node.js 18+ is used
2. Check `angular.json` configuration
3. Verify all dependencies are in `package.json`

---

## Cost Considerations

### Render (Free Tier)

- Free tier available with limitations
- Service may spin down after inactivity
- First request after spin-down takes ~30 seconds

### Vercel (Free Tier)

- Generous free tier for personal projects
- Automatic HTTPS
- Global CDN included

---

## Alternative Platforms

### Backend Alternatives

- **Railway**: Similar to Render, easy Python deployment
- **Fly.io**: Good free tier, global deployment
- **Google Cloud Run**: Serverless, pay-per-use

### Frontend Alternatives

- **Netlify**: Similar to Vercel, great for static sites
- **Cloudflare Pages**: Fast, generous free tier
- **GitHub Pages**: Free, but limited to static content

---

## Getting API Keys

### Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

### SerpAPI Key

1. Go to [SerpAPI](https://serpapi.com/)
2. Sign up for a free account
3. Copy your API key from the dashboard
