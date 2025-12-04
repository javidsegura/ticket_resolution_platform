import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCount = new Counter('requests');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users over 30 seconds
    { duration: '1m', target: 10 },    // Stay at 10 users for 1 minute
    { duration: '30s', target: 20 },   // Ramp up to 20 users over 30 seconds
    { duration: '1m', target: 20 },    // Stay at 20 users for 1 minute
    { duration: '30s', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.05'],    // Error rate should be less than 5%
},
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test health endpoint
  const healthResponse = http.get(`${BASE_URL}/api/health/ping`);
  const healthCheck = check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });

  errorRate.add(!healthCheck);
  responseTime.add(healthResponse.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test dependencies health endpoint
  const depsResponse = http.get(`${BASE_URL}/api/health/dependencies`);
  const depsCheck = check(depsResponse, {
    'dependencies check status is 200': (r) => r.status === 200,
    'dependencies check response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!depsCheck);
  responseTime.add(depsResponse.timings.duration);
  requestCount.add(1);

  sleep(1);
}
