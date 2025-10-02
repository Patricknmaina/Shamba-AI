import React, { useState, useEffect } from 'react';
import { Button, Card, Alert } from './components/ui';
import { LocationMap } from './components/LocationMap';
import { AdminLogin } from './components/AdminLogin';
import { AdminDashboard } from './components/AdminDashboard';
import { apiService } from './services/api';
import { authService } from './services/auth';
import loggingService, { logInteraction, logPageView, logFeatureUsage, setUserId, clearUserId, InteractionType, PageName, FeatureCategory } from './services/logging';
import type { AskResponse, InsightsResponse, Source } from './services/api';
import type { AdminUser } from './services/auth';
import { cn, getErrorMessage, getCropDisplayName, formatLatency, formatLatLon } from './lib/utils';
import { Sun, Moon, MapPin, MessageSquare, BarChart3, Settings, Copy, Check, ArrowRight, Globe, Brain, Shield, Users, TrendingUp, Leaf, Mail, Phone, MapPin as LocationIcon, Github, Twitter, Linkedin, ExternalLink } from 'lucide-react';

type Tab = 'about' | 'ask' | 'insights' | 'admin';
type Theme = 'light' | 'dark';

interface AskState {
  question: string;
  lang: string;
  topK: number;
  loading: boolean;
  response: AskResponse | null;
  error: string | null;
}

interface InsightsState {
  lat: number;
  lon: number;
  crop: string;
  lang: string;
  useMLForecast: boolean;
  loading: boolean;
  response: InsightsResponse | null;
  error: string | null;
}

interface AdminState {
  title: string;
  content: string;
  lang: string;
  country: string;
  loading: boolean;
  error: string | null;
  success: string | null;
}

const languages = [
  { value: 'en', label: 'English' },
  { value: 'sw', label: 'Swahili' },
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
  { value: 'pt', label: 'Portuguese' },
];

const defaultCrops = [
  'maize', 'beans', 'tomato', 'cassava', 'sweet_potato', 'banana', 'sorghum',
  'groundnut', 'onion', 'cabbage', 'chili', 'rice', 'wheat', 'barley'
];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('about');
  const [theme, setTheme] = useState<Theme>('light');
  const [crops, setCrops] = useState<string[]>(defaultCrops);
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean>(false);

  const [askState, setAskState] = useState<AskState>({
    question: '',
    lang: 'en',
    topK: 3,
    loading: false,
    response: null,
    error: null,
  });

  // Initialize logging with error handling
  useEffect(() => {
    try {
      // Set user ID if authenticated
      if (isAdminAuthenticated && adminUser) {
        setUserId(adminUser.id);
      } else {
        clearUserId();
      }

      // Log initial page view
      logPageView(PageName.ABOUT, 'ShambaAI - Agricultural Advisory Platform');
    } catch (error) {
      console.warn('Logging initialization failed:', error);
    }
  }, [isAdminAuthenticated, adminUser]);

  // Tab switching with logging
  const handleTabChange = (tab: Tab) => {
    try {
      // Log page navigation
      const pageNames = {
        'about': PageName.ABOUT,
        'ask': PageName.ASK,
        'insights': PageName.INSIGHTS,
        'admin': PageName.ADMIN
      };
      
      logInteraction({
        interactionType: InteractionType.NAVIGATE,
        pageName: pageNames[tab],
        actionName: 'tab_switch',
        resourceType: 'navigation',
        resourceId: tab,
        successStatus: true
      });
      
      logPageView(pageNames[tab], `ShambaAI - ${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
    } catch (error) {
      console.warn('Tab change logging failed:', error);
    }
    setActiveTab(tab);
  };

  const [insightsState, setInsightsState] = useState<InsightsState>({
    lat: -1.2921, // Nairobi coordinates
    lon: 36.8219,
    crop: 'maize',
    lang: 'en',
    useMLForecast: false,
    loading: false,
    response: null,
    error: null,
  });

  const [adminState, setAdminState] = useState<AdminState>({
    title: '',
    content: '',
    lang: 'en',
    country: 'Kenya',
    loading: false,
    error: null,
    success: null,
  });

  // Load theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  // Load crops from API and check admin authentication
  useEffect(() => {
    const loadCrops = async () => {
      try {
        const response = await apiService.getCrops();
        setCrops(response.crops);
      } catch (error) {
        console.warn('Failed to load crops from API, using defaults:', error);
      }
    };

    // Check admin authentication status
    const checkAdminAuth = () => {
      const isAuth = authService.isAuthenticated();
      setIsAdminAuthenticated(isAuth);
      if (isAuth) {
        const user = authService.getCurrentUser();
        setAdminUser(user);
      }
    };

    loadCrops();
    checkAdminAuth();
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(text);
      setTimeout(() => setCopiedText(null), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const handleAsk = async () => {
    if (!askState.question.trim()) return;

    setAskState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await apiService.ask({
        question: askState.question,
        lang: askState.lang,
        top_k: askState.topK,
      });

      setAskState(prev => ({
        ...prev,
        loading: false,
        response,
        error: null,
      }));
    } catch (error) {
      setAskState(prev => ({
        ...prev,
        loading: false,
        error: getErrorMessage(error),
      }));
    }
  };

  const handleGetInsights = async () => {
    setInsightsState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await apiService.getInsights({
        lat: insightsState.lat,
        lon: insightsState.lon,
        crop: insightsState.crop,
        lang: insightsState.lang,
        use_ml_forecast: insightsState.useMLForecast,
      });

      setInsightsState(prev => ({
        ...prev,
        loading: false,
        response,
        error: null,
      }));
    } catch (error) {
      setInsightsState(prev => ({
        ...prev,
        loading: false,
        error: getErrorMessage(error),
      }));
    }
  };

  const handleIndexDocument = async () => {
    if (!adminState.title.trim() || !adminState.content.trim()) return;

    setAdminState(prev => ({ ...prev, loading: true, error: null, success: null }));

    try {
      await apiService.indexDocument({
        title: adminState.title,
        text_md: adminState.content,
        lang: adminState.lang,
        country: adminState.country,
      });

      setAdminState(prev => ({
        ...prev,
        loading: false,
        success: 'Document submitted successfully!',
        error: null,
      }));
    } catch (error) {
      setAdminState(prev => ({
        ...prev,
        loading: false,
        error: getErrorMessage(error),
      }));
    }
  };

  // Admin authentication functions
  const handleAdminLogin = (user: AdminUser) => {
    setAdminUser(user);
    setIsAdminAuthenticated(true);
  };

  const handleAdminLogout = () => {
    authService.logout();
    setAdminUser(null);
    setIsAdminAuthenticated(false);
  };

  const renderAboutTab = () => (
    <div className="relative min-h-screen animate-fade-in">
      {/* Background Image with Overlay */}
      <div className="fixed inset-0 z-0">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: 'url(/crop_image.jpg)',
            filter: 'brightness(0.4) saturate(0.8)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
      </div>

      {/* Content */}
      <div className="relative z-10 space-y-16 pt-16 pb-32">
        {/* Hero Section */}
        <section className="relative p-8 md:p-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center max-w-4xl mx-auto">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-white/10 backdrop-blur-sm rounded-2xl mb-6 border border-white/20">
                <Leaf className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
                Empowering Farmers with
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-300 to-emerald-400"> AI-Powered Agriculture</span>
              </h1>
              <p className="text-xl md:text-2xl text-white/90 mb-8 leading-relaxed max-w-3xl mx-auto">
                ShambaAI combines cutting-edge artificial intelligence with local agricultural expertise to provide personalized farming advice, weather insights, and crop recommendations for sustainable agriculture.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button 
                  size="lg" 
                  onClick={() => handleTabChange('ask')}
                  className="group px-8 py-4 text-lg font-semibold bg-white text-gray-900 hover:bg-gray-100"
                >
                  Start Growing Better
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg"
                  onClick={() => handleTabChange('insights')}
                  className="px-8 py-4 text-lg font-semibold border-white text-white hover:bg-white hover:text-gray-900"
                >
                  Explore Insights
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="px-8 md:px-16">
          <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center hover:scale-105 transition-all duration-300 border border-white/20">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div className="text-3xl font-bold text-white mb-2">40+</div>
              <div className="text-white/80">Agricultural Documents</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center hover:scale-105 transition-all duration-300 border border-white/20">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div className="text-3xl font-bold text-white mb-2">2,044</div>
              <div className="text-white/80">Knowledge Chunks</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center hover:scale-105 transition-all duration-300 border border-white/20">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div className="text-3xl font-bold text-white mb-2">5</div>
              <div className="text-white/80">Languages Supported</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center hover:scale-105 transition-all duration-300 border border-white/20">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div className="text-3xl font-bold text-white mb-2">20+</div>
              <div className="text-white/80">Crop Types</div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="px-8 md:px-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Why Choose ShambaAI?
              </h2>
              <p className="text-xl text-white/80 max-w-2xl mx-auto">
                Our platform combines advanced AI technology with real-world agricultural expertise to deliver actionable insights.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-green-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  AI-Powered Insights
                </h3>
                <p className="text-white/80">
                  Get personalized farming advice powered by advanced machine learning and trained on thousands of agricultural documents.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-emerald-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Location-Based Recommendations
                </h3>
                <p className="text-white/80">
                  Receive tailored advice based on your specific location, soil conditions, and local weather patterns.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-blue-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Multilingual Support
                </h3>
                <p className="text-white/80">
                  Access information in English, Swahili, French, Spanish, and Portuguese to serve diverse farming communities.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-purple-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Weather & Soil Analysis
                </h3>
                <p className="text-white/80">
                  Get comprehensive weather forecasts and soil analysis to make informed farming decisions.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-orange-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Source Attribution
                </h3>
                <p className="text-white/80">
                  Every recommendation comes with verified sources from agricultural experts and research institutions.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:scale-105 transition-all duration-300 border border-white/20 border-l-4 border-l-red-400">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Sustainable Agriculture
                </h3>
                <p className="text-white/80">
                  Promote climate-smart farming practices that improve yields while protecting the environment.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="px-8 md:px-16">
          <div className="max-w-6xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-3xl p-8 md:p-16 border border-white/20">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                  How ShambaAI Works
                </h2>
                <p className="text-xl text-white/80 max-w-2xl mx-auto">
                  Our intelligent system processes your questions and location data to provide personalized agricultural guidance.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl border border-white/30">
                    1
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">
                    Ask Your Question
                  </h3>
                  <p className="text-white/80">
                    Simply ask any farming-related question in your preferred language. Our AI understands context and provides relevant answers.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl border border-white/30">
                    2
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">
                    Get Location Insights
                  </h3>
                  <p className="text-white/80">
                    Select your location on our interactive map to receive weather forecasts, soil analysis, and crop-specific recommendations.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl border border-white/30">
                    3
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">
                    Apply & Grow
                  </h3>
                  <p className="text-white/80">
                    Implement the recommendations and watch your crops thrive with data-driven farming practices and expert guidance.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );

  const renderAskTab = () => (
    <div className="relative min-h-screen animate-fade-in">
      {/* Background with Agricultural Theme */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-green-50 to-emerald-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900" />
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
      </div>

      {/* Content */}
      <div className="relative z-10 space-y-6 pt-8 pb-32">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Ask ShambaAI
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Get expert agricultural advice powered by AI and local knowledge
        </p>
      </div>

      <Card className="bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Your Question
            </label>
            <textarea
              value={askState.question}
              onChange={(e) => setAskState(prev => ({ ...prev, question: e.target.value }))}
              placeholder="Ask about farming, crops, soil, weather, or any agricultural topic..."
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 focus:border-slate-400 transition-colors duration-200 resize-vertical"
              rows={4}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Language
              </label>
              <select
                value={askState.lang}
                onChange={(e) => setAskState(prev => ({ ...prev, lang: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 focus:border-slate-400 transition-colors duration-200"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Number of Sources
              </label>
              <select
                value={askState.topK}
                onChange={(e) => setAskState(prev => ({ ...prev, topK: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 focus:border-slate-400 transition-colors duration-200"
              >
                {[1, 2, 3, 4, 5].map(num => (
                  <option key={num} value={num}>{num}</option>
                ))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleAsk}
            loading={askState.loading}
            disabled={!askState.question.trim()}
            className="w-full bg-slate-600 hover:bg-slate-700 text-white"
          >
            Ask Question
          </Button>
        </div>
      </Card>

      {askState.error && (
        <Alert variant="error">
          <strong>Error:</strong> {askState.error}
        </Alert>
      )}

      {askState.response && (
        <Card className="animate-scale-in bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-2 border-slate-300 dark:border-slate-600 shadow-xl">
          <div className="space-y-6">
            {/* Header Section */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-600">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                  <Brain className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    AI Response
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Powered by ShambaAI
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full">
                  <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    {formatLatency(askState.response.latency_ms)}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(askState.response!.answer)}
                  className="text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  {copiedText === askState.response.answer ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Answer Content */}
            <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-green-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 rounded-2xl border-2 border-slate-200 dark:border-slate-600 shadow-lg">
              {/* Decorative Elements */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-green-100 to-transparent dark:from-green-900/20 dark:to-transparent rounded-full -translate-y-16 translate-x-16 opacity-60"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-slate-100 to-transparent dark:from-slate-700/30 dark:to-transparent rounded-full translate-y-12 -translate-x-12 opacity-40"></div>
              
              {/* Content */}
              <div className="relative z-10 p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                    <Leaf className="w-4 h-4 text-white" />
                  </div>
                  <div className="h-6 w-px bg-slate-300 dark:bg-slate-600"></div>
                  <span className="text-sm font-medium text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30 px-3 py-1 rounded-full">
                    Agricultural AI Response
                  </span>
                </div>
                
                <div className="prose prose-slate max-w-none dark:prose-invert prose-headings:text-slate-900 dark:prose-headings:text-slate-100 prose-p:text-slate-800 dark:prose-p:text-slate-200 prose-strong:text-slate-900 dark:prose-strong:text-slate-100 prose-strong:font-semibold">
                  <div className="text-lg leading-8 whitespace-pre-wrap font-medium text-slate-800 dark:text-slate-200 tracking-wide">
                    {askState.response.answer}
                  </div>
                </div>
                
                {/* Bottom Accent */}
                <div className="mt-6 flex items-center space-x-2">
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                  <div className="px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full">
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                      Generated by ShambaAI
                    </span>
                  </div>
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                </div>
              </div>
            </div>

            {askState.response.sources.length > 0 && (
              <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-blue-200 dark:border-blue-800 shadow-lg">
                {/* Decorative Elements */}
                <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full -translate-y-12 -translate-x-12 opacity-50"></div>
                <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-tl from-indigo-100 to-transparent dark:from-indigo-900/20 dark:to-transparent rounded-full translate-y-16 translate-x-16 opacity-40"></div>
                
                {/* Content */}
                <div className="relative z-10 p-8">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                      <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div className="h-6 w-px bg-blue-300 dark:bg-blue-700"></div>
                    <div>
                      <h4 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                        Sources & References
                      </h4>
                      <p className="text-sm text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30 px-3 py-1 rounded-full inline-block mt-1">
                        Verified Agricultural Knowledge
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {askState.response.sources.map((source: Source, index: number) => (
                      <div key={index} className="group relative overflow-hidden bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-blue-200 dark:border-blue-700 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300 hover:shadow-md">
                        {/* Source Number Badge */}
                        <div className="absolute top-4 left-4 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-sm">
                          <span className="text-sm font-bold text-white">
                            {index + 1}
                          </span>
                        </div>
                        
                        <div className="p-6 pl-16">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-semibold text-slate-900 dark:text-slate-100 text-base mb-2 leading-tight">
                                {source.title}
                              </h5>
                              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                {source.snippet}
                              </p>
                            </div>
                            <div className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 hover:bg-blue-100 dark:hover:bg-blue-900/30"
                              >
                                <ExternalLink className="w-4 h-4 mr-1" />
                                <span className="text-xs font-medium">View</span>
                              </Button>
                            </div>
                          </div>
                        </div>
                        
                        {/* Subtle accent line */}
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-400 via-indigo-500 to-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Bottom Accent */}
                  <div className="mt-6 flex items-center space-x-2">
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-300 dark:via-blue-700 to-transparent"></div>
                    <div className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                      <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                        {askState.response.sources.length} Verified Source{askState.response.sources.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-300 dark:via-blue-700 to-transparent"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
      </div>
    </div>
  );

  const renderInsightsTab = () => (
    <div className="space-y-8 animate-fade-in pb-32">
      {/* Enhanced Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">
          Location Insights
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Get weather forecasts, soil data, and crop-specific recommendations for your selected location
        </p>
      </div>

      {/* Enhanced Layout with Better Map Visibility */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Map Section - Takes 2/3 of the width on large screens */}
        <div className="xl:col-span-2">
          <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-600 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full -translate-y-16 translate-x-16 opacity-60"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-slate-100 to-transparent dark:from-slate-700/30 dark:to-transparent rounded-full translate-y-12 -translate-x-12 opacity-40"></div>
            
            {/* Map Header */}
            <div className="relative z-10 p-6 border-b border-slate-200 dark:border-slate-600">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Interactive Location Map
                  </h3>
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    Click on the map to select your farming location
                  </p>
                </div>
              </div>
            </div>
            
            {/* Map Container with Enhanced Styling */}
            <div className="relative z-10 p-6">
              <div className="rounded-xl overflow-hidden shadow-lg border border-slate-200 dark:border-slate-600">
                <LocationMap
                  lat={insightsState.lat}
                  lon={insightsState.lon}
                  onLocationChange={(lat, lon) => setInsightsState(prev => ({ ...prev, lat, lon }))}
                />
              </div>
              
              {/* Current Location Display */}
              <div className="mt-4 p-4 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-slate-200 dark:border-slate-600">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-green-600 dark:text-green-400">📍</span>
                  </div>
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Selected Location:
                  </span>
                  <span className="text-sm font-mono text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">
                    {formatLatLon(insightsState.lat, insightsState.lon)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Panel - Takes 1/3 of the width on large screens */}
        <div className="xl:col-span-1">
          <div className="relative overflow-hidden bg-gradient-to-br from-green-50 via-white to-emerald-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-green-100 to-transparent dark:from-green-900/20 dark:to-transparent rounded-full -translate-y-12 -translate-x-12 opacity-50"></div>
            <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-tl from-emerald-100 to-transparent dark:from-emerald-900/20 dark:to-transparent rounded-full translate-y-16 translate-x-16 opacity-40"></div>
            
            {/* Settings Header */}
            <div className="relative z-10 p-6 border-b border-green-200 dark:border-green-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                  <Settings className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Location Settings
                  </h3>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    Configure your farming preferences
                  </p>
                </div>
              </div>
            </div>
            
            {/* Settings Content */}
            <div className="relative z-10 p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                  <Leaf className="w-4 h-4 inline mr-2" />
                  Crop Type
                </label>
                <select
                  value={insightsState.crop}
                  onChange={(e) => setInsightsState(prev => ({ ...prev, crop: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-green-200 dark:border-green-700 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 font-medium"
                >
                  {crops.map(crop => (
                    <option key={crop} value={crop}>
                      {getCropDisplayName(crop)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                  <Globe className="w-4 h-4 inline mr-2" />
                  Language
                </label>
                <select
                  value={insightsState.lang}
                  onChange={(e) => setInsightsState(prev => ({ ...prev, lang: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-green-200 dark:border-green-700 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 font-medium"
                >
                  {languages.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="p-4 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-green-200 dark:border-green-700">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="useMLForecast"
                    checked={insightsState.useMLForecast}
                    onChange={(e) => setInsightsState(prev => ({ ...prev, useMLForecast: e.target.checked }))}
                    className="h-5 w-5 text-green-600 focus:ring-green-500 border-green-300 rounded mt-0.5"
                  />
                  <div>
                    <label htmlFor="useMLForecast" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Advanced ML Forecasting
                    </label>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Get more detailed and accurate weather predictions
                    </p>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleGetInsights}
                loading={insightsState.loading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              >
                {insightsState.loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Analyzing Location...
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-5 h-5 mr-2" />
                    Get Location Insights
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {insightsState.error && (
        <Alert variant="error">
          <strong>Error:</strong> {insightsState.error}
        </Alert>
      )}

      {insightsState.response && (
        <div className="space-y-8 animate-scale-in">
          {/* Weather Forecast Section with Enhanced Styling */}
          <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-blue-200 dark:border-blue-800 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full -translate-y-16 translate-x-16 opacity-60"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-slate-100 to-transparent dark:from-slate-700/30 dark:to-transparent rounded-full translate-y-12 -translate-x-12 opacity-40"></div>
            
            {/* Weather Header */}
            <div className="relative z-10 p-6 border-b border-blue-200 dark:border-blue-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Weather Forecast
                  </h3>
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    {insightsState.response.forecast.model || '7-day Weather Forecast'}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Weather Content */}
            <div className="relative z-10 p-6">
              {insightsState.response.forecast.next_7_days ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Rainfall Card */}
                  <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl p-6 border border-blue-200 dark:border-blue-700">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                        <span className="text-lg">🌧️</span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-slate-100">Rainfall</h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Next 7 days</p>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                      {insightsState.response.forecast.next_7_days.total_rainfall_mm?.toFixed(1) || 'N/A'}mm
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Precipitation: {insightsState.response.forecast.next_7_days.precipitation_probability?.toFixed(0) || 'N/A'}% chance
                    </div>
                  </div>
                  
                  {/* Temperature Card */}
                  <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl p-6 border border-orange-200 dark:border-orange-700">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center">
                        <span className="text-lg">🌡️</span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-slate-100">Temperature</h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Average</p>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-orange-600 dark:text-orange-400 mb-2">
                      {insightsState.response.forecast.next_7_days.avg_temp_c?.toFixed(1) || 'N/A'}°C
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Optimal for {insightsState.response.crop || 'farming'}
                    </div>
                  </div>
                  
                  {/* Forecast Summary Card */}
                  <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl p-6 border border-green-200 dark:border-green-700">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                        <span className="text-lg">📊</span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-slate-100">Forecast Model</h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Data Source</p>
                      </div>
                    </div>
                    <div className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">
                      {insightsState.response.forecast.model || 'Weather API'}
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      {insightsState.response.forecast.next_7_days ? '7-day forecast' : 'Forecast data'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BarChart3 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <p className="text-slate-600 dark:text-slate-400">Weather forecast data not available</p>
                </div>
              )}
            </div>
          </div>

          {/* Soil Data Section with Enhanced Styling */}
          <div className="relative overflow-hidden bg-gradient-to-br from-green-50 via-white to-emerald-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-green-100 to-transparent dark:from-green-900/20 dark:to-transparent rounded-full -translate-y-12 -translate-x-12 opacity-50"></div>
            <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-tl from-emerald-100 to-transparent dark:from-emerald-900/20 dark:to-transparent rounded-full translate-y-16 translate-x-16 opacity-40"></div>
            
            {/* Soil Header */}
            <div className="relative z-10 p-6 border-b border-green-200 dark:border-green-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Soil Analysis
                  </h3>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    {insightsState.response.soil.source || 'Soil characteristics for your location'}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Soil Content */}
            <div className="relative z-10 p-6">
              {insightsState.response.soil.summary ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Basic Properties */}
                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center">
                      <span className="text-lg mr-2">🌱</span>
                      Basic Properties
                    </h4>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Texture:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100 capitalize">
                          {insightsState.response.soil.summary.texture || 'N/A'}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">pH Level:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.summary.pH || insightsState.response.soil.summary.ph || 'N/A'}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Organic Carbon:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.summary.organic_carbon_pct || 'N/A'}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Physical Properties */}
                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center">
                      <span className="text-lg mr-2">⚖️</span>
                      Physical Properties
                    </h4>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Sand:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.summary.sand_pct || 'N/A'}%
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Bulk Density:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.summary.bulk_density || 'N/A'} g/cm³
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">CEC:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.summary.cec || 'N/A'} cmol/kg
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Macronutrients */}
                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center">
                      <span className="text-lg mr-2">🧪</span>
                      Macronutrients
                    </h4>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Nitrogen:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.macronutrients?.nitrogen_pct || 'N/A'}%
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Phosphorus:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.macronutrients?.phosphorus_ppm || 'N/A'} ppm
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                        <span className="text-slate-600 dark:text-slate-400 font-medium">Potassium:</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {insightsState.response.soil.macronutrients?.potassium_ppm || 'N/A'} ppm
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MapPin className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                  <p className="text-slate-600 dark:text-slate-400">Soil data not available</p>
                </div>
              )}
            </div>
          </div>

          {/* Recommendations Section with Enhanced Styling */}
          <div className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-white to-pink-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-purple-200 dark:border-purple-800 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-purple-100 to-transparent dark:from-purple-900/20 dark:to-transparent rounded-full -translate-y-12 translate-x-12 opacity-50"></div>
            <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-pink-100 to-transparent dark:from-pink-900/20 dark:to-transparent rounded-full translate-y-16 -translate-x-16 opacity-40"></div>
            
            {/* Recommendations Header */}
            <div className="relative z-10 p-6 border-b border-purple-200 dark:border-purple-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    AI Recommendations
                  </h3>
                  <p className="text-sm text-purple-600 dark:text-purple-400">
                    Personalized farming tips based on your location and crop
                  </p>
                </div>
              </div>
            </div>
            
            {/* Recommendations Content */}
            <div className="relative z-10 p-6">
              <div className="space-y-4">
                {insightsState.response.tips.map((tip, index) => (
                  <div key={index} className="group relative overflow-hidden bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-purple-200 dark:border-purple-700 hover:border-purple-300 dark:hover:border-purple-600 transition-all duration-300 hover:shadow-md">
                    {/* Tip Number Badge */}
                    <div className="absolute top-4 left-4 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center shadow-sm">
                      <span className="text-sm font-bold text-white">
                        {index + 1}
                      </span>
                    </div>
                    
                    <div className="p-6 pl-16">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                            {tip}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Subtle accent line */}
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-400 via-pink-500 to-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </div>
                ))}
              </div>
              
              {/* Bottom Accent */}
              <div className="mt-6 flex items-center space-x-2">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-300 dark:via-purple-700 to-transparent"></div>
                <div className="px-4 py-2 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                    {insightsState.response.tips.length} AI-Generated Tip{insightsState.response.tips.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-300 dark:via-purple-700 to-transparent"></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAdminTab = () => (
    <div className="space-y-6 animate-fade-in pb-32">
      {/* Show login page if not authenticated */}
      {!isAdminAuthenticated ? (
        <AdminLogin onLoginSuccess={handleAdminLogin} />
      ) : (
        <>
          {/* Admin Dashboard */}
          {adminUser && <AdminDashboard user={adminUser} onLogout={handleAdminLogout} />}
          
          {/* Document Management Section */}
          <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-600 shadow-lg">
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full -translate-y-16 translate-x-16 opacity-60"></div>
            
            {/* Header */}
            <div className="relative z-10 p-6 border-b border-slate-200 dark:border-slate-600">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <Settings className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Document Management
                  </h2>
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    Add new agricultural documents to the knowledge base
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="relative z-10 p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Document Title
                  </label>
                  <input
                    type="text"
                    value={adminState.title}
                    onChange={(e) => setAdminState(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter document title..."
                    className="w-full px-4 py-3 border-2 border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 font-medium"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Content (Markdown)
                  </label>
                  <textarea
                    value={adminState.content}
                    onChange={(e) => setAdminState(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Enter document content in Markdown format..."
                    className="w-full px-4 py-3 border-2 border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-vertical font-medium"
                    rows={8}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                      Language
                    </label>
                    <select
                      value={adminState.lang}
                      onChange={(e) => setAdminState(prev => ({ ...prev, lang: e.target.value }))}
                      className="w-full px-4 py-3 border-2 border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 font-medium"
                    >
                      {languages.map(lang => (
                        <option key={lang.value} value={lang.value}>
                          {lang.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                      Country
                    </label>
                    <input
                      type="text"
                      value={adminState.country}
                      onChange={(e) => setAdminState(prev => ({ ...prev, country: e.target.value }))}
                      placeholder="Enter country..."
                      className="w-full px-4 py-3 border-2 border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 font-medium"
                    />
                  </div>
                </div>

                <Button
                  onClick={handleIndexDocument}
                  loading={adminState.loading}
                  disabled={!adminState.title.trim() || !adminState.content.trim()}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
                >
                  {adminState.loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Indexing Document...
                    </>
                  ) : (
                    <>
                      <Settings className="w-5 h-5 mr-2" />
                      Index Document
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Error and Success Messages */}
          {adminState.error && (
            <Alert variant="error">
              <strong>Error:</strong> {adminState.error}
            </Alert>
          )}

          {adminState.success && (
            <Alert variant="success">
              <strong>Success:</strong> {adminState.success}
            </Alert>
          )}
        </>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors duration-300">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-gray-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">🌱</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  ShambaAI
                </h1>
              </div>
            </div>

            <nav className="hidden md:flex space-x-1">
              <button
                onClick={() => handleTabChange('about')}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                  activeTab === 'about'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-700'
                )}
              >
                <Leaf className="h-4 w-4 mr-2 inline" />
                About
              </button>
              <button
                onClick={() => handleTabChange('ask')}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                  activeTab === 'ask'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-700'
                )}
              >
                <MessageSquare className="h-4 w-4 mr-2 inline" />
                Ask
              </button>
              <button
                onClick={() => handleTabChange('insights')}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                  activeTab === 'insights'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-700'
                )}
              >
                <BarChart3 className="h-4 w-4 mr-2 inline" />
                Insights
              </button>
              <button
                onClick={() => handleTabChange('admin')}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                  activeTab === 'admin'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-700'
                )}
              >
                <Settings className="h-4 w-4 mr-2 inline" />
                Admin
              </button>
            </nav>

            <div className="flex items-center space-x-2">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-700 transition-colors duration-200"
                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
              >
                {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'about' && renderAboutTab()}
        {activeTab === 'ask' && renderAskTab()}
        {activeTab === 'insights' && renderInsightsTab()}
        {activeTab === 'admin' && renderAdminTab()}
      </main>

      {/* Footer */}
      <footer className="relative z-20 bg-slate-900 dark:bg-slate-950 border-t border-slate-800 dark:border-slate-900 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Company Info */}
            <div className="lg:col-span-1">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Leaf className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">ShambaAI</h3>
              </div>
              <p className="text-gray-400 mb-4 text-sm leading-relaxed">
                Empowering farmers with AI-powered agricultural insights, weather forecasts, and sustainable farming practices.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  <Github className="w-5 h-5" />
                </a>
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  <Twitter className="w-5 h-5" />
                </a>
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  <Linkedin className="w-5 h-5" />
                </a>
              </div>
            </div>

            {/* Features */}
            <div>
              <h4 className="text-white font-semibold mb-4">Features</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" onClick={(e) => { e.preventDefault(); handleTabChange('ask'); }} className="text-gray-400 hover:text-primary-400 transition-colors text-sm flex items-center">
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Ask Questions
                  </a>
                </li>
                <li>
                  <a href="#" onClick={(e) => { e.preventDefault(); handleTabChange('insights'); }} className="text-gray-400 hover:text-primary-400 transition-colors text-sm flex items-center">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Location Insights
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm flex items-center">
                    <Globe className="w-4 h-4 mr-2" />
                    Multilingual Support
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm flex items-center">
                    <Brain className="w-4 h-4 mr-2" />
                    AI Recommendations
                  </a>
                </li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm">
                    API Reference
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm">
                    Best Practices
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm">
                    Crop Guide
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors text-sm">
                    Weather Alerts
                  </a>
                </li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-white font-semibold mb-4">Contact</h4>
              <ul className="space-y-3">
                <li className="flex items-center text-gray-400 text-sm">
                  <Mail className="w-4 h-4 mr-3 text-primary-400" />
                  <a href="mailto:info@shambaai.com" className="hover:text-primary-400 transition-colors">
                    info@shambaai.com
                  </a>
                </li>
                <li className="flex items-center text-gray-400 text-sm">
                  <Phone className="w-4 h-4 mr-3 text-primary-400" />
                  <a href="tel:+254700000000" className="hover:text-primary-400 transition-colors">
                    +254 700 000 000
                  </a>
                </li>
                <li className="flex items-start text-gray-400 text-sm">
                  <LocationIcon className="w-4 h-4 mr-3 text-primary-400 mt-0.5" />
                  <span>
                    Nairobi, Kenya<br />
                    East Africa
                  </span>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Section */}
          <div className="border-t border-slate-800 dark:border-slate-900 mt-12 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="text-gray-400 text-sm mb-4 md:mb-0">
                &copy; 2024 ShambaAI. All rights reserved. Empowering farmers with AI-powered agricultural insights.
              </div>
              <div className="flex flex-wrap gap-6 text-sm">
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  Privacy Policy
                </a>
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  Terms of Service
                </a>
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors">
                  Cookie Policy
                </a>
                <a href="#" className="text-gray-400 hover:text-primary-400 transition-colors flex items-center">
                  Support
                  <ExternalLink className="w-3 h-3 ml-1" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;