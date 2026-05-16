# 🚀 Quick Reference - Akshar Light Deployment

## ✅ What's Ready

Your project is **100% ready** for Railway deployment with:
- ✅ MongoDB Atlas integration
- ✅ Environment variable configuration
- ✅ CORS setup for production
- ✅ Railway configuration files
- ✅ All code pushed to GitHub

## 📋 Deployment Checklist

### Step 1: Deploy Backend (5 minutes)
1. Go to https://railway.app
2. New Project → GitHub → `samarthchavda/akshar_light`
3. Settings → Root Directory → `backend`
4. Variables → Add:
   ```
   MONGODB_URL=mongodb+srv://StudyPoint:Cb3oog9A97jZO6cH@cluster0.whyvvvy.mongodb.net/akshar_light?retryWrites=true&w=majority&appName=Cluster0
   ```
5. Settings → Networking → Generate Domain
6. **Copy the backend URL** 📝

### Step 2: Deploy Frontend (5 minutes)
1. Same Railway project → New Service → GitHub
2. Settings → Root Directory → `frontend`
3. Variables → Add:
   ```
   VITE_API_URL=<paste-backend-url-here>
   ```
4. Settings → Networking → Generate Domain
5. **Copy the frontend URL** 📝

### Step 3: Update Backend (2 minutes)
1. Go to backend service
2. Variables → Add:
   ```
   FRONTEND_URL=<paste-frontend-url-here>
   ```
3. Click "Redeploy"

### Step 4: Test (1 minute)
1. Open backend URL + `/api/health` → Should see `{"status":"ok"}`
2. Open frontend URL → Should see login page
3. Create account → Test invoice creation

## 🔗 Important URLs

**GitHub Repository:**
https://github.com/samarthchavda/akshar_light

**MongoDB Atlas:**
- Connection String: `mongodb+srv://StudyPoint:Cb3oog9A97jZO6cH@cluster0.whyvvvy.mongodb.net/akshar_light`
- Database: `akshar_light`
- Collections: `invoices`, `users`

**Railway:**
- Dashboard: https://railway.app/dashboard
- Backend URL: (generate after deployment)
- Frontend URL: (generate after deployment)

## 📝 Environment Variables Quick Copy

### Backend
```
MONGODB_URL=mongodb+srv://StudyPoint:Cb3oog9A97jZO6cH@cluster0.whyvvvy.mongodb.net/akshar_light?retryWrites=true&w=majority&appName=Cluster0
FRONTEND_URL=https://your-frontend.railway.app
```

### Frontend
```
VITE_API_URL=https://your-backend.railway.app
```

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check Railway logs, verify MONGODB_URL is set |
| Frontend can't connect | Verify VITE_API_URL is correct, check CORS |
| PDF generation fails | Check Railway logs for WeasyPrint errors |
| CORS errors | Make sure FRONTEND_URL is set in backend and redeployed |
| MongoDB connection fails | Check MongoDB Atlas network access (allow 0.0.0.0/0) |

## 📚 Full Documentation

- **Detailed Guide**: [RAILWAY_SETUP.md](./RAILWAY_SETUP.md)
- **Deployment Info**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Setup Summary**: [SETUP_COMPLETE.md](./SETUP_COMPLETE.md)
- **Project README**: [README.md](./README.md)

## ⏱️ Estimated Time

- **Total deployment time**: ~15 minutes
- **Backend deployment**: 5 minutes
- **Frontend deployment**: 5 minutes
- **Configuration**: 3 minutes
- **Testing**: 2 minutes

## 🎯 Success Criteria

✅ Backend health endpoint returns `{"status":"ok"}`
✅ Frontend loads without errors
✅ Can create user account
✅ Can create and preview invoice
✅ Can download PDF

## 💡 Pro Tips

1. **Save URLs**: Keep backend and frontend URLs handy
2. **Check Logs**: Railway logs are your friend for debugging
3. **MongoDB Atlas**: Make sure network access allows Railway IPs
4. **CORS**: Always redeploy backend after adding FRONTEND_URL
5. **Environment Variables**: Double-check spelling and format

## 🔄 Update Process

When you make code changes:
1. Push to GitHub: `git push origin main`
2. Railway auto-deploys (watch the logs)
3. Changes live in ~2-3 minutes

## 📞 Need Help?

1. Check [RAILWAY_SETUP.md](./RAILWAY_SETUP.md) troubleshooting section
2. Review Railway deployment logs
3. Verify all environment variables
4. Check MongoDB Atlas connection

---

**Ready to deploy?** Start with Step 1 above! 🚀
