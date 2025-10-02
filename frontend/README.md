# ShambaAI Frontend

A modern React TypeScript frontend for the ShambaAI agricultural advisory platform, built with Vite, Tailwind CSS, and React Leaflet for interactive mapping.

## 🌟 Features

- **Modern React Architecture**: Built with React 18, TypeScript, and Vite for optimal performance
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Interactive Maps**: Location selection using React Leaflet with OpenStreetMap
- **Multilingual Support**: Interface supports multiple languages (English, Swahili, French, Spanish, Portuguese)
- **Dark/Light Theme**: Toggle between themes with persistent storage
- **Real-time API Integration**: Seamless integration with the ShambaAI ML backend
- **Comprehensive Error Handling**: User-friendly error messages and loading states
- **Accessibility**: Built with accessibility best practices

## 🏗️ Architecture

### Tech Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v3
- **Maps**: React Leaflet with OpenStreetMap
- **Icons**: Lucide React
- **State Management**: React Hooks (useState, useEffect)
- **HTTP Client**: Fetch API with custom error handling

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui.tsx              # Reusable UI components
│   │   └── LocationMap.tsx     # Interactive map component
│   ├── services/
│   │   └── api.ts              # API service layer
│   ├── lib/
│   │   └── utils.ts            # Utility functions
│   ├── App.tsx                 # Main application component
│   ├── main.tsx                # Application entry point
│   └── style.css               # Global styles and Tailwind
├── public/
├── index.html
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── package.json
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- ShambaAI ML backend running on `http://localhost:8000`

### Installation

1. **Clone and navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables** (optional):
   Create a `.env` file in the frontend directory:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_API_KEY=supersecretapexkey
   VITE_DEV_MODE=true
   VITE_DEBUG_MODE=false
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```

5. **Open your browser** and navigate to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 📱 Features Overview

### 1. Ask Page
- **Question Input**: Large textarea for agricultural questions
- **Language Selection**: Choose from 5 supported languages
- **Source Control**: Configure number of sources (1-5)
- **Real-time Responses**: AI-powered answers with source attribution
- **Copy Functionality**: Copy answers to clipboard

### 2. Insights Page
- **Interactive Map**: Click to select locations or use GPS
- **Coordinate Input**: Manual latitude/longitude entry
- **Crop Selection**: Choose from supported crop types
- **ML Forecasting**: Optional ML-powered weather forecasting
- **Comprehensive Data**: Weather, soil, and recommendation cards

### 3. Admin Page
- **Document Management**: Add new agricultural documents
- **Markdown Support**: Rich text input with Markdown
- **Metadata**: Language and country selection
- **API Integration**: Submit documents to the knowledge base

## 🎨 Design System

### Color Palette
- **Primary**: Green tones (#10b981) for agricultural theme
- **Secondary**: Slate grays for neutral elements
- **Success**: Green for positive feedback
- **Warning**: Yellow for cautions
- **Error**: Red for errors
- **Info**: Blue for information

### Typography
- **Font Family**: Inter (system fallbacks)
- **Headings**: Bold weights for hierarchy
- **Body Text**: Regular weight for readability

### Components
- **Cards**: Elevated containers with shadows
- **Buttons**: Multiple variants (primary, secondary, outline, ghost)
- **Forms**: Consistent input styling with validation states
- **Alerts**: Contextual feedback messages
- **Badges**: Small status indicators

## 🌐 API Integration

### Endpoints
- `POST /ask` - Submit questions for AI responses
- `GET /insights` - Get location-based agricultural insights
- `POST /index_doc` - Submit new documents (admin)
- `GET /crops` - Get supported crop list
- `GET /health` - Health check endpoint

### Authentication
All API requests include the `x-api-key` header for authentication.

### Error Handling
- Network errors with retry suggestions
- API errors with user-friendly messages
- Loading states for all async operations

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 640px (single column, compact navigation)
- **Tablet**: 640px - 1023px (two columns, full navigation)
- **Desktop**: ≥ 1024px (multi-column layout, full features)

### Mobile Optimizations
- Touch-friendly buttons and inputs
- Optimized map interaction
- Collapsible navigation
- Swipe-friendly interfaces

## 🎯 Accessibility

### Features
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Proper ARIA labels
- **Color Contrast**: WCAG AA compliant
- **Focus Management**: Visible focus indicators
- **Semantic HTML**: Proper heading hierarchy

### Testing
- Test with keyboard-only navigation
- Verify screen reader compatibility
- Check color contrast ratios
- Validate ARIA implementations

## 🔧 Development

### Code Quality
- **TypeScript**: Strict type checking
- **ESLint**: Code linting (if configured)
- **Prettier**: Code formatting (if configured)
- **Component Architecture**: Reusable, composable components

### Performance
- **Code Splitting**: Automatic with Vite
- **Tree Shaking**: Unused code elimination
- **Bundle Optimization**: Minification and compression
- **Lazy Loading**: Components loaded on demand

## 🚀 Deployment

### Environment Variables
Configure these environment variables for production:

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_API_KEY=your-production-api-key
VITE_DEV_MODE=false
```

### Build Optimization
- Assets are automatically optimized
- CSS is purged of unused styles
- JavaScript is minified and compressed
- Images are optimized

### Hosting Options
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **CDN**: CloudFlare, AWS CloudFront
- **Traditional**: Apache, Nginx

## 🧪 Testing

### Manual Testing Checklist
- [ ] All pages load correctly
- [ ] Navigation works on all screen sizes
- [ ] Forms submit successfully
- [ ] Map interaction functions properly
- [ ] Theme toggle persists
- [ ] API integration works
- [ ] Error states display correctly
- [ ] Loading states show appropriately

### Browser Compatibility
- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile Browsers**: iOS Safari, Chrome Mobile
- **Minimum Versions**: ES2022 support required

## 🐛 Troubleshooting

### Common Issues

1. **Build Errors**:
   - Ensure Node.js 18+ is installed
   - Clear `node_modules` and reinstall
   - Check TypeScript configuration

2. **API Connection Issues**:
   - Verify backend is running on correct port
   - Check API key configuration
   - Ensure CORS is properly configured

3. **Map Not Loading**:
   - Check internet connection
   - Verify Leaflet CSS is loaded
   - Ensure proper API keys for map tiles

4. **Styling Issues**:
   - Verify Tailwind CSS is properly configured
   - Check PostCSS configuration
   - Ensure CSS imports are correct

### Debug Mode
Enable debug mode by setting `VITE_DEBUG_MODE=true` in your environment variables.

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Leaflet Documentation](https://react-leaflet.js.org/)
- [Vite Guide](https://vitejs.dev/guide/)

## 🤝 Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test on multiple screen sizes
4. Ensure accessibility compliance
5. Update documentation for new features

## 📄 License

This project is part of the ShambaAI agricultural advisory platform.

---

**Built with ❤️ for farmers and agricultural communities**

