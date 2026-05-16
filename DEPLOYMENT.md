# Akshar Light - Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository with the code

## Backend Deployment

1. **Create a new Railway project**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `akshar_light` repository

2. **Configure Backend Service**
   - Railway will auto-detect the backend
   - Set the root directory to `/backend`
   - Add environment variables:
     ```
     MONGODB_URL=mongodb+srv://StudyPoint:Cb3oog9A97jZO6cH@cluster0.whyvvvy.mongodb.net/akshar_light?retryWrites=true&w=majority&appName=Cluster0
     PORT=8000
     ```

3. **Deploy Backend**
   - Railway will automatically deploy
   - Note the backend URL (e.g., `https://your-backend.railway.app`)

## Frontend Deployment

1. **Add Frontend Service**
   - In the same Railway project, click "New Service"
   - Select "Deploy from GitHub repo"
   - Choose the same repository
   - Set root directory to `/frontend`

2. **Configure Frontend Service**
   - Add environment variable:
     ```
     VITE_API_URL=https://your-backend.railway.app
     ```
   - Set build command: `npm run build`
   - Set start command: `npm run preview`

3. **Update Backend CORS**
   - Go to backend service settings
   - Add environment variable:
     ```
     FRONTEND_URL=https://your-frontend.railway.app
     ```
   - Redeploy backend

## Alternative: Single Service Deployment

You can also deploy both as a single service by creating a simple proxy setup, but the two-service approach is recommended for better separation.

## MongoDB Atlas Setup

The MongoDB connection is already configured. Make sure:
- Your MongoDB Atlas cluster is accessible from anywhere (0.0.0.0/0) or add Railway IPs
- The database name is `akshar_light`
- Collections will be created automatically

## Post-Deployment

1. Test the backend health endpoint: `https://your-backend.railway.app/api/health`
2. Access the frontend: `https://your-frontend.railway.app`
3. Create an account and start using the application

## Environment Variables Summary

### Backend
- `MONGODB_URL`: MongoDB Atlas connection string
- `PORT`: Port number (Railway sets this automatically)
- `FRONTEND_URL`: Frontend URL for CORS

### Frontend
- `VITE_API_URL`: Backend API URL

## Troubleshooting

- If PDF generation fails, check Railway logs for WeasyPrint dependencies
- If CORS errors occur, verify FRONTEND_URL is set correctly in backend
- For MongoDB connection issues, check the connection string and network access in Atlas
