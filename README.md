# Akshar Light Billing System

A modern billing and invoice management system with Gujarati language support, featuring React frontend and FastAPI backend with PDF generation capabilities.

![Status](https://img.shields.io/badge/status-ready%20for%20deployment-green)
![MongoDB](https://img.shields.io/badge/database-MongoDB%20Atlas-green)
![Railway](https://img.shields.io/badge/deploy-Railway-purple)

## 🌟 Features

- ✅ **Invoice Management** - Create, edit, and manage invoices
- ✅ **Letter Pad Template** - Professional letter writing with company letterhead
- ✅ **Gujarati Support** - Full support for Gujarati language with custom fonts
- ✅ **PDF Generation** - High-quality PDF export with WeasyPrint
- ✅ **User Authentication** - Multi-user support with localStorage
- ✅ **MongoDB Integration** - Cloud database with MongoDB Atlas
- ✅ **Railway Ready** - Pre-configured for Railway deployment

## 📁 Project Structure

```
akshar_light/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main application (MongoDB integrated)
│   │   └── templates/      # Jinja2 templates
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile           # Railway process file
│   ├── railway.toml       # Railway configuration
│   └── nixpacks.toml      # Build configuration
├── frontend/               # React frontend
│   ├── src/
│   │   └── App.jsx        # Main React component
│   ├── package.json       # Node dependencies
│   ├── vite.config.js     # Vite configuration
│   └── railway.toml       # Railway configuration
├── RAILWAY_SETUP.md       # Detailed deployment guide
├── DEPLOYMENT.md          # General deployment info
└── README.md              # This file
```

## 🚀 Quick Start - Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (or local MongoDB)

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install WeasyPrint system dependencies (macOS)**
   ```bash
   brew install pango cairo gdk-pixbuf glib libffi
   ```

4. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env and add your MongoDB URL
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**
   ```bash
   npm run dev
   ```

3. **Open browser**
   - Navigate to http://localhost:5173
   - Create an account and start using the app

## 🌐 Deploy to Railway

**Ready to deploy?** Follow the detailed step-by-step guide:

👉 **[Open RAILWAY_SETUP.md](./RAILWAY_SETUP.md)** for complete deployment instructions

### Quick Deploy Summary

1. Deploy backend to Railway
2. Set `MONGODB_URL` environment variable
3. Deploy frontend to Railway
4. Set `VITE_API_URL` to backend URL
5. Update backend with `FRONTEND_URL`
6. Done! 🎉

## 🔧 Environment Variables

### Backend
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/akshar_light
PORT=8000
FRONTEND_URL=https://your-frontend.railway.app
```

### Frontend
```env
VITE_API_URL=https://your-backend.railway.app
```

## 📚 API Endpoints

- `GET /` - Health check page
- `GET /api/health` - API health status
- `POST /api/invoice/html` - Generate invoice HTML preview
- `POST /api/invoice/pdf` - Generate invoice PDF
- `POST /api/template/render` - Render custom template
- `POST /api/template/pdf` - Generate template PDF

## 🛠️ Technology Stack

**Frontend:**
- React 18
- Vite
- Modern CSS

**Backend:**
- FastAPI
- WeasyPrint (PDF generation)
- Jinja2 (templating)
- PyMongo (MongoDB driver)

**Database:**
- MongoDB Atlas

**Deployment:**
- Railway

## 📖 Documentation

- **[RAILWAY_SETUP.md](./RAILWAY_SETUP.md)** - Step-by-step Railway deployment guide
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - General deployment information
- **[SETUP_COMPLETE.md](./SETUP_COMPLETE.md)** - Setup completion summary

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is private and proprietary.

## 👤 Author

Samarth Chavda

## 🆘 Support

If you encounter any issues:
1. Check the [RAILWAY_SETUP.md](./RAILWAY_SETUP.md) troubleshooting section
2. Review Railway logs for errors
3. Verify all environment variables are set correctly
4. Check MongoDB Atlas network access settings

---

**Status**: ✅ Ready for Production Deployment
**Repository**: https://github.com/samarthchavda/akshar_light
