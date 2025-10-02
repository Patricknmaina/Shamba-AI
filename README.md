# Shamba-AI: AI-Powered Agricultural Advisory Platform

A comprehensive agricultural advisory system that leverages artificial intelligence, machine learning, and multilingual support to provide personalized farming guidance to smallholder farmers in East Africa and beyond.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Frontend Application](#frontend-application)
- [Database Setup](#database-setup)
- [Machine Learning Components](#machine-learning-components)
- [Multilingual Support](#multilingual-support)
- [Security](#security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

Shamba-AI is an intelligent agricultural advisory platform designed to bridge the knowledge gap for smallholder farmers in East Africa. The system combines advanced machine learning models, comprehensive agricultural knowledge bases, and multilingual capabilities to deliver practical, location-specific farming advice.

### Mission

To democratize access to agricultural knowledge and expertise through AI-powered tools that are accessible, accurate, and culturally relevant for farmers worldwide.

### Target Users

- Smallholder farmers in East Africa
- Agricultural extension workers
- Agricultural researchers and educators
- Farming cooperatives and organizations

## Key Features

### Core Capabilities

- **AI-Powered Q&A System**: Advanced RAG (Retrieval-Augmented Generation) system that answers agricultural questions using comprehensive knowledge bases
- **Location-Based Insights**: ML-powered agricultural recommendations based on specific geographic coordinates
- **Multilingual Support**: Full interface and content support for 8 languages including English, Swahili, French, Spanish, Portuguese, Arabic, German, and Italian
- **Weather Forecasting**: Integration with meteorological data and ML-based rainfall prediction models
- **Soil Analysis**: XGBoost-powered soil quality assessment and recommendations
- **Crop-Specific Guidance**: Tailored advice for multiple crop types including maize, beans, cassava, groundnuts, onions, cabbage, and chili peppers
- **Interactive Maps**: Location selection and visualization using React Leaflet
- **Admin Dashboard**: Comprehensive administrative interface for content management and user analytics

### Advanced Features

- **RAG System**: Retrieval-Augmented Generation using FAISS vector search and OpenAI GPT-4o-mini
- **Semantic Search**: Advanced document retrieval using sentence transformers and OpenAI embeddings
- **ML Forecasting**: Prophet-based rainfall forecasting for agricultural planning
- **Real-time Analytics**: User interaction tracking and system performance monitoring
- **Responsive Design**: Mobile-first design optimized for various devices
- **Dark/Light Theme**: User preference management with persistent theme selection

## System Architecture

Shamba-AI follows a modern microservices architecture with three primary components:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│              TypeScript + Tailwind CSS                   │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/HTTPS
┌─────────────────▼───────────────────────────────────────┐
│                FastAPI Backend                          │
│            ML Service + API Gateway                     │
└─────────────────┬───────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│ Oracle  │  │   ML     │  │External  │
│Database │  │ Models   │  │  APIs    │
└─────────┘  └──────────┘  └──────────┘
```

### Component Overview

1. **Frontend Application**: React-based user interface with TypeScript and Tailwind CSS
2. **ML Service**: FastAPI-based backend providing AI capabilities and API endpoints
3. **Oracle Database**: Comprehensive data storage with user management and analytics
4. **External Services**: Integration with OpenAI, weather APIs, and mapping services

## Technology Stack

### Backend Technologies

- **Framework**: FastAPI (Python 3.9+)
- **Database**: Oracle Autonomous Database
- **ML Libraries**: 
  - OpenAI GPT-4o-mini for text generation
  - OpenAI text-embedding-3-small for embeddings
  - FAISS for vector similarity search
  - Prophet for time series forecasting
  - XGBoost for soil quality prediction
  - scikit-learn for additional ML tasks
- **Data Processing**: Pandas, NumPy, SciPy
- **Authentication**: JWT with BCrypt password hashing
- **API Documentation**: Automatic OpenAPI/Swagger generation

### Frontend Technologies

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v3
- **Maps**: React Leaflet with OpenStreetMap
- **Icons**: Lucide React
- **State Management**: React Hooks
- **HTTP Client**: Native Fetch API with custom error handling

### Infrastructure

- **Containerization**: Docker support
- **Environment Management**: Python virtual environments
- **Configuration**: Environment variables with .env files
- **Version Control**: Git with comprehensive .gitignore

## Project Structure

```
Shamba-AI/
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── services/          # API and authentication services
│   │   ├── lib/               # Utility functions
│   │   └── App.tsx            # Main application component
│   ├── public/                # Static assets
│   ├── package.json           # Frontend dependencies
│   └── README.md              # Frontend documentation
├── ml_service/                 # FastAPI ML backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   ├── database/          # Database connection and models
│   │   ├── services/          # Business logic services
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── retrieval.py       # RAG retrieval service
│   │   ├── llm_openai.py      # OpenAI integration
│   │   ├── insights_generator.py # ML insights generation
│   │   ├── rainfall_forecast.py # Weather forecasting
│   │   ├── soil_xgboost_model.py # Soil analysis ML model
│   │   └── translate_simple.py # Multilingual translation
│   ├── tools/                 # Utility scripts
│   │   ├── convert_pdfs.py    # PDF to Markdown converter
│   │   └── build_index.py     # FAISS index builder
│   ├── data/                  # ML data and models
│   │   ├── corpus/            # Document corpus (Markdown)
│   │   ├── embeddings.npy     # Pre-computed embeddings
│   │   ├── faiss.index        # FAISS vector index
│   │   ├── models/            # Trained ML models
│   │   └── soil_data/         # Soil analysis datasets
│   ├── tests/                 # Test suites
│   ├── requirements.txt       # Python dependencies
│   └── README.md              # ML service documentation
├── database/                   # Database setup and schemas
│   ├── complete_schema.sql    # Complete database schema
│   ├── test_connection.py     # Database connection testing
│   └── Database Setup.md      # Database setup guide
├── farming_docs/              # Agricultural knowledge base
│   └── *.pdf                  # PDF documents for RAG system
├── requirements.txt           # Global Python dependencies
├── setup.sh                   # Automated setup script
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- Oracle Autonomous Database (for production)
- OpenAI API key
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Shamba-AI
```

### 2. Backend Setup

```bash
# Run the automated setup script
./setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Configuration

Create `ml_service/.env` file with required configuration:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
ML_API_KEY=supersecretapexkey

# Database (Optional for development)
ORACLE_USER=ADMIN
ORACLE_PASSWORD=your_password
ORACLE_DSN=your_dsn
ORACLE_WALLET_LOCATION=/path/to/wallet

# Service Configuration
ML_PORT=8000
DATA_DIR=./data

# JWT Security
JWT_SECRET_KEY=your_32_character_secret_key
```

### 5. Build Knowledge Base

```bash
cd ml_service/tools

# Convert PDFs to Markdown
python convert_pdfs.py --input ../../farming_docs --output ../data/corpus

# Build FAISS index
python build_index.py --corpus ../data/corpus --output ../data
```

### 6. Start Services

```bash
# Terminal 1: Start ML backend
cd ml_service
source ../.venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 7. Access the Application

- Frontend: http://localhost:5173
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Installation

### Detailed Backend Installation

1. **Python Environment Setup**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **System Dependencies** (if needed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev build-essential
   
   # macOS
   brew install python3-dev
   ```

3. **Oracle Database Client** (for production):
   ```bash
   pip install cx_Oracle
   # Download Oracle Instant Client and wallet files
   ```

### Frontend Installation

1. **Node.js Setup**:
   ```bash
   # Install Node.js 18+ from https://nodejs.org/
   node --version  # Should be 18+
   npm --version
   ```

2. **Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

## Configuration

### Environment Variables

#### Required Variables

- `OPENAI_API_KEY`: Your OpenAI API key for GPT and embeddings
- `ML_API_KEY`: API key for securing ML service endpoints

#### Optional Variables

- `ML_PORT`: Port for ML service (default: 8000)
- `DATA_DIR`: Directory for ML data files (default: ./data)
- `ORACLE_*`: Database connection parameters (for production)

### Database Configuration

For production deployment with Oracle Autonomous Database:

1. **Download Wallet**: Get database wallet from Oracle Cloud Console
2. **Configure Connection**: Update `.env` with database credentials
3. **Run Schema**: Execute `database/complete_schema.sql` in SQL Developer
4. **Test Connection**: Run `python database/test_connection.py`

### Frontend Configuration

Create `frontend/.env` for custom configuration:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=supersecretapexkey
VITE_DEV_MODE=true
```

## API Documentation

### Core Endpoints

#### POST /ask
Answer agricultural questions using RAG system.

**Request**:
```json
{
  "question": "When should I plant maize?",
  "lang": "en",
  "top_k": 3
}
```

**Response**:
```json
{
  "answer": "Maize should be planted at the onset of the rainy season...",
  "sources": [
    {
      "title": "Maize Planting Guide",
      "snippet": "Plant maize when soil moisture is adequate...",
      "url": ""
    }
  ],
  "latency_ms": 2340
}
```

#### GET /insights
Get location-based agricultural insights.

**Parameters**:
- `lat`: Latitude (-90 to 90)
- `lon`: Longitude (-180 to 180)
- `crop`: Crop type (maize, beans, cassava, etc.)
- `lang`: Language code (default: en)
- `use_ml_forecast`: Use Prophet ML forecast (optional)

**Response**:
```json
{
  "forecast": {
    "next_5_days": {
      "rainfall_mm": 45,
      "temp_avg_c": 24,
      "humidity_pct": 65
    },
    "recommendation": "Conditions suitable for planting"
  },
  "soil": {
    "texture": "loam",
    "ph": 6.5,
    "organic_carbon_pct": 2.1,
    "recommendation": "Good soil quality"
  },
  "tips": [
    "Moderate rainfall expected (45mm). Good conditions for maize growth.",
    "Soil pH (6.5) is optimal for maize. Maintain with organic matter."
  ]
}
```

#### GET /crops
List supported crop types for insights endpoint.

**Response**:
```json
{
  "crops": ["maize", "beans", "cassava", "groundnut", "onion", "cabbage", "chili"]
}
```

#### GET /health
Service health check and statistics.

**Response**:
```json
{
  "status": "healthy",
  "index_loaded": true,
  "num_documents": 15,
  "num_chunks": 237,
  "translation_available": true
}
```

### Authentication

All endpoints except `/` and `/health` require API key authentication via `X-API-Key` header.

## Frontend Application

### Features Overview

#### 1. Ask Page
- **Question Input**: Large textarea for agricultural questions
- **Language Selection**: Choose from 8 supported languages
- **Source Control**: Configure number of sources (1-5)
- **Real-time Responses**: AI-powered answers with source attribution
- **Copy Functionality**: Copy answers to clipboard

#### 2. Insights Page
- **Interactive Map**: Click to select locations or use GPS
- **Coordinate Input**: Manual latitude/longitude entry
- **Crop Selection**: Choose from supported crop types
- **ML Forecasting**: Optional ML-powered weather forecasting
- **Comprehensive Data**: Weather, soil, and recommendation cards

#### 3. Admin Page
- **Document Management**: Add new agricultural documents
- **Markdown Support**: Rich text input with Markdown
- **Metadata**: Language and country selection
- **API Integration**: Submit documents to the knowledge base

### Design System

#### Color Palette
- **Primary**: Green tones (#10b981) for agricultural theme
- **Secondary**: Slate grays for neutral elements
- **Success**: Green for positive feedback
- **Warning**: Yellow for cautions
- **Error**: Red for errors
- **Info**: Blue for information

#### Typography
- **Font Family**: Inter with system fallbacks
- **Headings**: Bold weights for hierarchy
- **Body Text**: Regular weight for readability

#### Components
- **Cards**: Elevated containers with shadows
- **Buttons**: Multiple variants (primary, secondary, outline, ghost)
- **Forms**: Consistent input styling with validation states
- **Alerts**: Contextual feedback messages
- **Badges**: Small status indicators

### Responsive Design

#### Breakpoints
- **Mobile**: < 640px (single column, compact navigation)
- **Tablet**: 640px - 1023px (two columns, full navigation)
- **Desktop**: ≥ 1024px (multi-column layout, full features)

#### Mobile Optimizations
- Touch-friendly buttons and inputs
- Optimized map interaction
- Collapsible navigation
- Swipe-friendly interfaces

## Database Setup

### Oracle Autonomous Database

The system uses Oracle Autonomous Database for production data storage with comprehensive schema including:

#### Admin Authentication System
- **admin_users**: Administrative user accounts with role-based access
- **user_sessions**: JWT session management
- **audit_log**: Complete security audit trail
- **system_config**: System configuration parameters
- **password_reset_tokens**: Password reset functionality

#### User Analytics System
- **user_interactions**: Every user interaction tracked
- **page_views**: Page analytics and behavior
- **feature_usage**: Feature usage statistics
- **api_requests**: API performance monitoring
- **error_logs**: Error tracking and debugging
- **user_preferences**: User settings and preferences

### Database Features

#### Security
- BCrypt password hashing
- JWT session management
- Account lockout after failed attempts
- Complete audit trail
- Role-based access control

#### Performance
- 40+ optimized indexes
- Automatic timestamp triggers
- Efficient foreign key relationships
- Connection pooling support

#### Maintenance
- Built-in cleanup procedures
- Statistics gathering
- Health check queries
- Size monitoring

### Setup Instructions

1. **Create Database Connection**:
   ```bash
   # Download wallet from Oracle Cloud Console
   # Extract to secure location
   # Update .env with connection details
   ```

2. **Import Schema**:
   ```bash
   # Open SQL Developer
   # Connect to "Shamba Database 2"
   # Run database/complete_schema.sql
   # Verify with database/VERIFY_DATABASE.sql
   ```

3. **Test Connection**:
   ```bash
   python database/test_connection.py
   ```

## Machine Learning Components

### RAG System (Retrieval-Augmented Generation)

The core AI system combines semantic search with large language models:

#### Architecture
```
User Question → Translation → Embedding → FAISS Search → Context → LLM → Translation → Answer
```

#### Components
1. **Embedding Service**: OpenAI text-embedding-3-small (1536 dimensions)
2. **Vector Search**: FAISS IndexFlatIP for cosine similarity
3. **Generation**: OpenAI GPT-4o-mini for answer generation
4. **Translation**: GPT-4o-mini for multilingual support

#### Knowledge Base
- **Documents**: 40+ PDF agricultural documents
- **Format**: Converted to Markdown with metadata
- **Chunking**: 500-word chunks with 75-word overlap
- **Index**: FAISS vector index with 200+ chunks

### Weather Forecasting

#### Prophet ML Model
- **Purpose**: Rainfall forecasting for agricultural planning
- **Input**: Historical weather data
- **Output**: 14-day rainfall predictions
- **Features**: Trend analysis, seasonality detection

#### Integration
- **Open-Meteo API**: Current weather data
- **Location-based**: Coordinates-specific forecasts
- **Crop-specific**: Recommendations based on crop requirements

### Soil Analysis

#### XGBoost Model
- **Purpose**: Soil quality prediction and recommendations
- **Features**: pH, organic carbon, texture, nutrients
- **Output**: Soil quality scores and improvement recommendations

#### Data Sources
- **Spatial Database**: Global soil datasets
- **Interpolation**: Location-based soil characteristic estimation
- **Validation**: Cross-referenced with local soil data

### Crop-Specific Models

#### Supported Crops
- Maize, Beans, Cassava, Groundnuts
- Onions, Cabbage, Chili peppers
- Extensible framework for additional crops

#### Model Features
- **Growth Requirements**: Temperature, rainfall, soil conditions
- **Planting Calendar**: Optimal timing recommendations
- **Pest/Disease**: Common issues and prevention
- **Yield Optimization**: Best practices for maximum production

## Multilingual Support

### Supported Languages

1. **English** (en) - Primary language
2. **Swahili** (sw) - East African region
3. **French** (fr) - West African region
4. **Spanish** (es) - Latin American region
5. **Portuguese** (pt) - Brazilian region
6. **Arabic** (ar) - Middle East/North Africa
7. **German** (de) - European region
8. **Italian** (it) - European region

### Translation Architecture

#### Process Flow
```
User Input (Any Language) → Translate to English → Process → Generate Answer → Translate to User Language → Response
```

#### Implementation
- **Translation Service**: GPT-4o-mini for high-quality translation
- **Language Detection**: Automatic detection when not specified
- **Context Preservation**: Maintains agricultural terminology
- **Fallback**: English responses if translation fails

### Localization Features

#### Interface Localization
- Complete UI translation
- Date/time formatting
- Number formatting
- Currency display

#### Content Localization
- Agricultural terminology
- Regional crop varieties
- Local farming practices
- Cultural context adaptation

## Security

### Authentication & Authorization

#### API Security
- **API Key Authentication**: Required for all endpoints
- **JWT Tokens**: Secure session management
- **Rate Limiting**: Prevents abuse
- **CORS Configuration**: Controlled cross-origin access

#### User Management
- **BCrypt Hashing**: Secure password storage
- **Account Lockout**: Protection against brute force
- **Session Management**: Automatic token expiration
- **Role-based Access**: Granular permissions

### Data Protection

#### Encryption
- **In Transit**: HTTPS/TLS encryption
- **At Rest**: Database encryption
- **API Keys**: Secure storage and transmission
- **Passwords**: BCrypt with salt

#### Privacy
- **User Data**: Minimal data collection
- **Analytics**: Anonymized usage statistics
- **Logs**: No sensitive information logging
- **GDPR Compliance**: Data protection best practices

### Infrastructure Security

#### Network Security
- **Firewall Rules**: Restricted port access
- **VPC Configuration**: Private network isolation
- **SSL Certificates**: Validated certificates
- **DDoS Protection**: Traffic filtering

#### Monitoring
- **Audit Logs**: Complete activity tracking
- **Error Monitoring**: Real-time error detection
- **Performance Monitoring**: System health tracking
- **Security Alerts**: Automated threat detection

## Testing

### Backend Testing

#### Unit Tests
```bash
cd ml_service
python -m pytest tests/
```

#### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "x-api-key: supersecretapexkey" \
  -d '{"question": "When should I plant maize?", "lang": "en", "top_k": 3}'

# Get insights
curl "http://localhost:8000/insights?lat=-1.2921&lon=36.8219&crop=maize&lang=en" \
  -H "x-api-key: supersecretapexkey"
```

#### Database Testing
```bash
python database/test_connection.py
```

### Frontend Testing

#### Manual Testing Checklist
- [ ] All pages load correctly
- [ ] Navigation works on all screen sizes
- [ ] Forms submit successfully
- [ ] Map interaction functions properly
- [ ] Theme toggle persists
- [ ] API integration works
- [ ] Error states display correctly
- [ ] Loading states show appropriately

#### Browser Compatibility
- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile Browsers**: iOS Safari, Chrome Mobile
- **Minimum Versions**: ES2022 support required

### Integration Testing

#### End-to-End Tests
1. **User Registration/Login**: Complete authentication flow
2. **Question Asking**: RAG system integration
3. **Insights Generation**: ML model integration
4. **Multilingual Support**: Translation pipeline
5. **Admin Functions**: Document management

#### Performance Testing
- **Load Testing**: Concurrent user simulation
- **Response Time**: API endpoint performance
- **Memory Usage**: Resource consumption monitoring
- **Database Performance**: Query optimization

## Deployment

### Production Deployment

#### Backend Deployment

1. **Environment Setup**:
   ```bash
   # Production server setup
   sudo apt update
   sudo apt install python3.9 python3.9-venv nginx
   
   # Create production user
   sudo useradd -m shambaai
   sudo su - shambaai
   ```

2. **Application Deployment**:
   ```bash
   # Clone repository
   git clone <repository-url>
   cd Shamba-AI
   
   # Setup environment
   python3.9 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   cp ml_service/.env.example ml_service/.env
   # Edit .env with production values
   ```

3. **Database Configuration**:
   ```bash
   # Install Oracle client
   pip install cx_Oracle
   
   # Download and configure wallet
   # Update .env with database credentials
   
   # Import schema
   # Run database/complete_schema.sql
   ```

4. **Service Configuration**:
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/shambaai.service
   
   # Start service
   sudo systemctl enable shambaai
   sudo systemctl start shambaai
   ```

#### Frontend Deployment

1. **Build Application**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Nginx Configuration**:
   ```bash
   # Configure nginx
   sudo nano /etc/nginx/sites-available/shambaai
   
   # Enable site
   sudo ln -s /etc/nginx/sites-available/shambaai /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **SSL Certificate**:
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Obtain certificate
   sudo certbot --nginx -d your-domain.com
   ```

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ml_service/ ./ml_service/
COPY data/ ./data/

# Set environment variables
ENV PYTHONPATH=/app
ENV ML_PORT=8000

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "uvicorn", "ml_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ML_API_KEY=${ML_API_KEY}
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### Cloud Deployment

#### AWS Deployment
1. **EC2 Instance**: Launch Ubuntu 20.04 LTS
2. **RDS Oracle**: Set up managed Oracle database
3. **Application Load Balancer**: Distribute traffic
4. **CloudFront**: CDN for frontend assets
5. **Route 53**: DNS management

#### Azure Deployment
1. **Virtual Machine**: Ubuntu-based VM
2. **Azure Database**: Managed Oracle service
3. **Application Gateway**: Load balancing
4. **CDN**: Content delivery network
5. **DNS**: Azure DNS management

#### Google Cloud Deployment
1. **Compute Engine**: Ubuntu VM instance
2. **Cloud SQL**: Managed database service
3. **Load Balancer**: Traffic distribution
4. **Cloud CDN**: Content delivery
5. **Cloud DNS**: Domain management

### Monitoring & Maintenance

#### Application Monitoring
- **Health Checks**: Automated service monitoring
- **Performance Metrics**: Response time tracking
- **Error Tracking**: Real-time error monitoring
- **Log Aggregation**: Centralized logging

#### Database Monitoring
- **Connection Pool**: Monitor database connections
- **Query Performance**: Slow query identification
- **Storage Usage**: Disk space monitoring
- **Backup Status**: Automated backup verification

#### Security Monitoring
- **Access Logs**: User access tracking
- **Failed Logins**: Security threat detection
- **API Usage**: Rate limiting monitoring
- **Certificate Status**: SSL certificate monitoring

## Contributing

### Development Setup

1. **Fork Repository**: Create your fork on GitHub
2. **Clone Fork**: `git clone <your-fork-url>`
3. **Create Branch**: `git checkout -b feature/your-feature`
4. **Setup Environment**: Follow installation instructions
5. **Make Changes**: Implement your feature
6. **Test Changes**: Run test suite
7. **Submit PR**: Create pull request

### Code Standards

#### Python Code
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations
- **Docstrings**: Document functions and classes
- **Error Handling**: Comprehensive exception handling

#### TypeScript Code
- **ESLint**: Follow configured linting rules
- **Prettier**: Consistent code formatting
- **Type Safety**: Use TypeScript features
- **Component Structure**: Follow React best practices

### Pull Request Process

1. **Feature Branch**: Create descriptive branch name
2. **Commit Messages**: Use conventional commit format
3. **Test Coverage**: Ensure adequate test coverage
4. **Documentation**: Update relevant documentation
5. **Code Review**: Address reviewer feedback
6. **Merge**: Squash and merge to main

### Issue Reporting

#### Bug Reports
- **Clear Description**: Detailed problem description
- **Reproduction Steps**: Step-by-step reproduction
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: System and version information

#### Feature Requests
- **Use Case**: Clear use case description
- **Proposed Solution**: Suggested implementation
- **Alternatives**: Other possible solutions
- **Additional Context**: Relevant background information

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Summary

```
MIT License

Copyright (c) 2025 Patrick Maina

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**Built with dedication for farmers and agricultural communities worldwide.**

For support, questions, or contributions, please open an issue on GitHub or contact the development team.

*Last Updated: January 2025*
*Version: 1.0.0*
