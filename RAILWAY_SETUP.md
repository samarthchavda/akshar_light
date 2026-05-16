# Railway Deployment - Step by Step Guide

## 🚀 Quick Start

Your project is now ready to deploy on Railway! Follow these steps:

## Step 1: Deploy Backend

1. **Go to Railway** (https://railway.app)
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `samarthchavda/akshar_light`

2. **Configure Backend Service**
   - Railway will detect your project
   - Click on the service
   - Go to "Settings" → "Root Directory"
   - Set to: `backend`

3. **Add Environment Variables**
   - Go to "Variables" tab
   - Add these variables:
   
   ```
   MONGODB_URL=mongodb+srv://StudyPoint:Cb3oog9A97jZO6cH@cluster0.whyvvvy.mongodb.net/akshar_light?retryWrites=true&w=majority&appName=Cluster0
   ```

4. **Generate Domain**
   - Go to "Settings" → "Networking"
   - Click "Generate Domain"
   - Copy the URL (e.g., `https://akshar-backend-production.up.railway.app`)
   - **Save this URL - you'll need it for frontend!**

5. **Deploy**
   - Railway will automatically deploy
   - Wait for deployment to complete
   - Check logs for any errors

## Step 2: Deploy Frontend

1. **Add New Service**
   - In the same Railway project
   - Click "+ New"
   - Select "GitHub Repo"
   - Choose the same `samarthchavda/akshar_light` repository

2. **Configure Frontend Service**
   - Click on the new service
   - Go to "Settings" → "Root Directory"
   - Set to: `frontend`

3. **Add Environment Variables**
   - Go to "Variables" tab
   - Add this variable (use the backend URL from Step 1):
   
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```
   
   Replace `your-backend-url.railway.app` with your actual backend URL!

4. **Configure Build Settings**
   - Railway will auto-detect the build
   - It should use:
     - Build Command: `npm run build`
     - Start Command: `npm run preview`

5. **Generate Domain**
   - Go to "Settings" → "Networking"
   - Click "Generate Domain"
   - Copy the URL (e.g., `https://akshar-frontend-production.up.railway.app`)

6. **Update Backend CORS**
   - Go back to your **backend service**
   - Go to "Variables" tab
   - Add this variable (use the frontend URL you just generated):
   
   ```
   FRONTEND_URL=https://your-frontend-url.railway.app
   ```

7. **Redeploy Backend**
   - Go to backend service
   - Click "Deploy" → "Redeploy"

## Step 3: Test Your Deployment

1. **Test Backend**
   - Open: `https://your-backend-url.railway.app/api/health`
   - You should see: `{"status":"ok"}`

2. **Test Frontend**
   - Open: `https://your-frontend-url.railway.app`
   - You should see the login page
   - Create an account and test creating an invoice

## 🔧 Troubleshooting

### Backend Issues

**Problem: MongoDB connection fails**
- Check if MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
- Verify the MONGODB_URL is correct
- Check Railway logs for connection errors

**Problem: PDF generation fails**
- Check Railway logs for WeasyPrint errors
- The nixpacks.toml should handle dependencies automatically
- If issues persist, check the Railway build logs

**Problem: 500 errors**
- Check Railway logs for Python errors
- Verify all environment variables are set
- Check if the PORT variable is set (Railway sets this automatically)

### Frontend Issues

**Problem: Can't connect to backend**
- Verify VITE_API_URL is set correctly
- Make sure it includes `https://` and no trailing slash
- Check browser console for CORS errors

**Problem: CORS errors**
- Make sure FRONTEND_URL is set in backend
- Verify backend has been redeployed after adding FRONTEND_URL
- Check backend logs for CORS-related messages

**Problem: Build fails**
- Check if all dependencies are in package.json
- Verify node version compatibility
- Check Railway build logs

### General Issues

**Problem: Service won't start**
- Check Railway logs for startup errors
- Verify the start command is correct
- Check if PORT environment variable is being used

**Problem: Changes not reflecting**
- Make sure you pushed changes to GitHub
- Railway auto-deploys on push to main branch
- You can manually trigger a deploy from Railway dashboard

## 📝 Important Notes

1. **MongoDB Atlas**: The database is already configured. Collections will be created automatically when you first use the app.

2. **Environment Variables**: Make sure all environment variables are set correctly. Missing variables will cause deployment failures.

3. **CORS**: The backend is configured to allow all origins (`*`) for Railway deployment. For production, you should restrict this to your frontend URL only.

4. **Costs**: Railway offers a free tier with limited resources. Monitor your usage to avoid unexpected charges.

5. **Custom Domains**: You can add custom domains in Railway settings if you have one.

## 🎉 Success!

Once both services are deployed and configured:
- Your backend will be at: `https://your-backend.railway.app`
- Your frontend will be at: `https://your-frontend.railway.app`
- MongoDB is connected and ready to store data

You can now share the frontend URL with users!

## 📞 Support

If you encounter issues:
1. Check Railway logs first
2. Verify all environment variables
3. Check GitHub repository for latest code
4. Review the DEPLOYMENT.md file for additional details
