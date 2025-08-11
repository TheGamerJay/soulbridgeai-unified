# SoulBridge AI Frontend

A React frontend application for SoulBridge AI that connects to the Flask backend.

## 🚀 Features

- **Backend Connection**: Tests connectivity to the SoulBridge AI backend
- **Modern React**: Built with Vite for fast development and builds
- **Responsive Design**: Mobile-friendly interface
- **SoulBridge Branding**: Styled to match the SoulBridge AI theme
- **API Health Check**: Displays backend connection status

## 🛠️ Development Setup

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Start development server:**
```bash
npm run dev
```

3. **Open browser:**
Visit `http://localhost:5173` to see the application

## 📦 Building for Production

1. **Create production build:**
```bash
npm run build
```

2. **Preview production build locally:**
```bash
npm run preview
```

## 🌐 Deployment Options

### Option 1: Railway
1. Build the project: `npm run build`
2. Upload the `dist/` folder contents to Railway
3. Configure Railway to serve static files

### Option 2: Vercel
1. Connect your Git repository to Vercel
2. Vercel will automatically detect it's a Vite project
3. Deploy with default settings

### Option 3: Netlify
1. Build the project: `npm run build`
2. Drag and drop the `dist/` folder to Netlify
3. Or connect your Git repository for continuous deployment

### Option 4: GitHub Pages
1. Build the project: `npm run build`
2. Use `gh-pages` package to deploy the `dist/` folder

## 🔧 Configuration

### Backend API URL
The frontend is configured to connect to:
- **Main Domain**: `https://soulbridgeai.com` (Your primary website)
- **API endpoint**: `/health` for connection testing
- **Full App**: Complete SoulBridge AI experience with all companions

To change the backend URL, update the fetch URL in `src/App.jsx`:
```javascript
fetch('https://your-backend-url.com/health')
```

### Environment Variables
Create a `.env` file in the root directory:
```
VITE_API_URL=https://soulbridgeai.com
```

Then use in your code:
```javascript
fetch(`${import.meta.env.VITE_API_URL}/health`)
```

## 📁 Project Structure

```
soulbridgeai-frontend/
├── public/
│   ├── favicon.ico          # SoulBridge logo
│   └── index.html           # HTML template
├── src/
│   ├── App.jsx              # Main React component
│   ├── App.css              # SoulBridge AI styles
│   └── main.jsx             # Vite entry point
├── package.json             # Dependencies and scripts
└── vite.config.js           # Vite configuration
```

## 🎨 Styling

The application uses a dark theme with SoulBridge AI branding:
- **Primary Colors**: Cyan (#22d3ee), Blue (#3b82f6), Purple (#8b5cf6)
- **Background**: Dark gradient (1e1e2f → 2e2e4f → 1a1a2e)
- **Typography**: Segoe UI, modern and clean
- **Animations**: Subtle glows and hover effects

## 🔗 Backend Integration

Currently connects to:
- **Health Check**: `GET /health` - Tests backend connectivity
- **Future endpoints**: Can be easily extended for chat, authentication, etc.

## 📱 Responsive Design

The frontend is fully responsive and works on:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🚀 Next Steps

1. Add authentication pages (login/register)
2. Implement chat interface
3. Add character selection
4. Integrate voice chat features
5. Add theme customization
6. Implement real-time messaging

## 📄 License

Part of the SoulBridge AI project.