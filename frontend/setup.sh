#!/bin/bash

# ShambaAI Frontend Setup Script

echo "🌱 Setting up ShambaAI Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating environment configuration..."
    cat > .env << EOF
# ShambaAI Frontend Environment Variables

# Backend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=supersecretapexkey

# Development Configuration
VITE_DEV_MODE=true
VITE_DEBUG_MODE=false
EOF
    echo "✅ Environment file created (.env)"
else
    echo "✅ Environment file already exists"
fi

# Test build
echo "🔨 Testing build process..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi

echo "✅ Build successful"

# Clean up dist folder (optional)
echo "🧹 Cleaning up build artifacts..."
rm -rf dist

echo ""
echo "🎉 ShambaAI Frontend setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure the ShambaAI ML backend is running on http://localhost:8000"
echo "2. Start the development server: npm run dev"
echo "3. Open http://localhost:5173 in your browser"
echo ""
echo "Available commands:"
echo "  npm run dev      - Start development server"
echo "  npm run build    - Build for production"
echo "  npm run preview  - Preview production build"
echo ""
echo "Happy farming! 🌾"

