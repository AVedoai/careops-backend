# Railway Deployment Guide for CareOps Backend

## Pre-deployment Checklist
- ✅ Procfile created (web + worker processes)
- ✅ requirements.txt updated with all dependencies
- ✅ railway.json configured for multi-service deployment  
- ✅ .dockerignore created to exclude unnecessary files
- ✅ runtime.txt specifies Python version
- ✅ Environment variables template ready

## Step-by-Step Deployment

### 1. Prepare Repository
```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your backend repository
5. Railway will automatically detect the Procfile

### 3. Add Database Services
1. Click "Add Service" → "Database" → "PostgreSQL"
2. Click "Add Service" → "Database" → "Redis"  
3. Wait for both to provision (2-3 minutes)

### 4. Configure Environment Variables
1. Go to your main service settings
2. Click "Variables" tab
3. Add all variables from `.env.template`:

**Critical Variables:**
- `DATABASE_URL` - Copy from PostgreSQL service
- `REDIS_URL` - Copy from Redis service
- `SECRET_KEY` - Generate new secret for production
- `ENVIRONMENT=production`
- `DEBUG=False`
- `CORS_ORIGINS` - Update with your frontend domain
- `FRONTEND_URL` - Your Vercel app URL
- `BACKEND_URL` - Will be provided by Railway

**Integration Keys (copy from local .env):**
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL` 
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

### 5. Deploy
1. Railway will auto-deploy when you push to GitHub
2. Check deployment logs for any issues
3. Both web and worker processes should start

### 6. Database Migration
Run this once after first deployment:
```bash
# In Railway's service console or locally with production DB URL
alembic upgrade head
```

### 7. Test Deployment
- Visit your Railway URL: `https://your-app.up.railway.app/health`
- Should return: `{"status":"healthy"}`
- Test a few API endpoints to confirm everything works

### 8. Update Frontend Configuration
Update your frontend's API URL to point to Railway:
```env
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

## Troubleshooting

**Common Issues:**
- **Build fails**: Check requirements.txt for correct package versions
- **Connection errors**: Verify DATABASE_URL and REDIS_URL are correct
- **CORS errors**: Update CORS_ORIGINS with exact frontend domain
- **Worker not starting**: Check Procfile syntax and Celery app path

**Monitoring:**
- Railway provides logs for both web and worker processes
- Monitor Celery tasks in Railway logs
- Check database connections and Redis connectivity

## Production Best Practices
- Use production-grade secrets (not development ones)
- Enable Railway's auto-deploy on GitHub pushes
- Monitor application metrics in Railway dashboard
- Set up log aggregation for better debugging
- Consider enabling Railway's health checks

Your backend will be accessible at: `https://your-app.up.railway.app`