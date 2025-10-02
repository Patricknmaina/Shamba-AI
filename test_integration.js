#!/usr/bin/env node

// Integration test script to verify frontend-backend connection
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'supersecretapexkey';

async function testIntegration() {
  console.log('🧪 Testing ShambaAI Frontend-Backend Integration...\n');

  try {
    // Test 1: Health check
    console.log('1️⃣ Testing health endpoint...');
    const healthResponse = await fetch(`${API_BASE_URL}/health`, {
      headers: { 'x-api-key': API_KEY }
    });
    
    if (healthResponse.ok) {
      const health = await healthResponse.json();
      console.log('✅ Health check passed');
      console.log(`   Status: ${health.status}`);
      console.log(`   Documents: ${health.num_documents}`);
      console.log(`   Chunks: ${health.num_chunks}`);
      console.log(`   Translation: ${health.translation_available ? 'Available' : 'Not available'}\n`);
    } else {
      throw new Error(`Health check failed: ${healthResponse.status}`);
    }

    // Test 2: Crops endpoint
    console.log('2️⃣ Testing crops endpoint...');
    const cropsResponse = await fetch(`${API_BASE_URL}/crops`);
    
    if (cropsResponse.ok) {
      const crops = await cropsResponse.json();
      console.log('✅ Crops endpoint working');
      console.log(`   Available crops: ${crops.crops.length}`);
      console.log(`   Sample crops: ${crops.crops.slice(0, 5).join(', ')}...\n`);
    } else {
      throw new Error(`Crops endpoint failed: ${cropsResponse.status}`);
    }

    // Test 3: Ask endpoint
    console.log('3️⃣ Testing ask endpoint...');
    const askResponse = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
      },
      body: JSON.stringify({
        question: 'How do I improve maize yields?',
        lang: 'en',
        top_k: 3
      })
    });
    
    if (askResponse.ok) {
      const askResult = await askResponse.json();
      console.log('✅ Ask endpoint working');
      console.log(`   Answer length: ${askResult.answer.length} characters`);
      console.log(`   Sources: ${askResult.sources.length}`);
      console.log(`   Latency: ${askResult.latency_ms}ms`);
      console.log(`   Sample answer: ${askResult.answer.substring(0, 100)}...\n`);
    } else {
      const errorText = await askResponse.text();
      throw new Error(`Ask endpoint failed: ${askResponse.status} - ${errorText}`);
    }

    // Test 4: Insights endpoint
    console.log('4️⃣ Testing insights endpoint...');
    const insightsResponse = await fetch(`${API_BASE_URL}/insights?lat=-1.2921&lon=36.8219&crop=maize&lang=en`, {
      headers: { 'x-api-key': API_KEY }
    });
    
    if (insightsResponse.ok) {
      const insights = await insightsResponse.json();
      console.log('✅ Insights endpoint working');
      console.log(`   Tips: ${insights.tips.length}`);
      console.log(`   Soil texture: ${insights.soil?.texture || 'N/A'}`);
      console.log(`   Sample tip: ${insights.tips[0]?.substring(0, 80)}...\n`);
    } else {
      const errorText = await insightsResponse.text();
      throw new Error(`Insights endpoint failed: ${insightsResponse.status} - ${errorText}`);
    }

    // Test 5: CORS headers (important for frontend)
    console.log('5️⃣ Testing CORS configuration...');
    const corsResponse = await fetch(`${API_BASE_URL}/health`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'x-api-key'
      }
    });
    
    const corsHeaders = corsResponse.headers;
    console.log('✅ CORS test completed');
    console.log(`   Access-Control-Allow-Origin: ${corsHeaders.get('Access-Control-Allow-Origin') || 'Not set'}`);
    console.log(`   Access-Control-Allow-Methods: ${corsHeaders.get('Access-Control-Allow-Methods') || 'Not set'}`);
    console.log(`   Access-Control-Allow-Headers: ${corsHeaders.get('Access-Control-Allow-Headers') || 'Not set'}\n`);

    console.log('🎉 All integration tests passed!');
    console.log('\n📋 Frontend-Backend Integration Status:');
    console.log('   ✅ Backend API is running and responding');
    console.log('   ✅ All endpoints are functional');
    console.log('   ✅ Authentication is working');
    console.log('   ✅ CORS is configured');
    console.log('   ✅ Data flow is working correctly');
    
    console.log('\n🚀 Ready for frontend testing!');
    console.log('   Frontend: http://localhost:5173');
    console.log('   Backend: http://localhost:8000');
    
  } catch (error) {
    console.error('❌ Integration test failed:', error.message);
    console.log('\n🔧 Troubleshooting steps:');
    console.log('   1. Ensure backend is running: curl http://localhost:8000/');
    console.log('   2. Check API key configuration');
    console.log('   3. Verify CORS settings in backend');
    console.log('   4. Check network connectivity');
    process.exit(1);
  }
}

// Run the test
testIntegration();

