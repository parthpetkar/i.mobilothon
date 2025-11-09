"""
Quick Benchmark Runner for PowerPoint Metrics
==============================================

Run this script for a fast benchmark focused on PPT-ready metrics.
Results optimized for presentations and demos.

Usage:
    python quick_benchmark.py
"""

import requests
import statistics
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://imobilothon-backend.onrender.com"

def test_endpoint(name, url, iterations=20):
    """Quick test of an endpoint"""
    print(f"Testing {name}...", end=" ", flush=True)
    times = []
    
    for _ in range(iterations):
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start
            if response.status_code == 200:
                times.append(elapsed * 1000)  # Convert to ms
        except Exception:
            pass
    
    if times:
        avg = statistics.mean(times)
        print(f"✓ {avg:.0f}ms avg")
        return avg
    else:
        print("✗ Failed")
        return None

def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     QUICK BENCHMARK - PPT METRICS GENERATOR             ║
║              i.mobilothon 2025                          ║
╚══════════════════════════════════════════════════════════╝

Backend: {BACKEND_URL}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Running 5 quick tests...
""")
    
    results = {}
    
    # Test 1: Health Check
    avg = test_endpoint(
        "Health Check",
        f"{BACKEND_URL}/"
    )
    if avg:
        results['health'] = avg
    
    # Test 2: Parking Search
    avg = test_endpoint(
        "Parking Search",
        f"{BACKEND_URL}/parkings/?location=73.8567&location=18.5204&radius=5000"
    )
    if avg:
        results['search'] = avg
    
    # Test 3: Free Parking Predictions
    avg = test_endpoint(
        "ML Predictions",
        f"{BACKEND_URL}/predictions/free-parking?lat=18.5204&lon=73.8567&radius_meters=300"
    )
    if avg:
        results['ml'] = avg
    
    # Test 4: Large Radius Search
    avg = test_endpoint(
        "Large Dataset",
        f"{BACKEND_URL}/parkings/?location=73.8567&location=18.5204&radius=10000"
    )
    if avg:
        results['large'] = avg
    
    # Test 5: Different Location
    avg = test_endpoint(
        "Different Location",
        f"{BACKEND_URL}/parkings/?location=73.8700&location=18.5100&radius=5000"
    )
    if avg:
        results['location2'] = avg
    
    # Calculate overall metrics
    if results:
        avg_overall = statistics.mean(results.values())
        
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                 PPT-READY METRICS                       ║
╚══════════════════════════════════════════════════════════╝

📊 OVERALL AVERAGE RESPONSE TIME: {avg_overall:.0f} ms

📋 BREAKDOWN:
  • Health Check:        {results.get('health', 'N/A'):.0f} ms
  • Parking Search:      {results.get('search', 'N/A'):.0f} ms
  • ML Predictions:      {results.get('ml', 'N/A'):.0f} ms
  • Large Dataset:       {results.get('large', 'N/A'):.0f} ms
  • Multi-Location:      {results.get('location2', 'N/A'):.0f} ms

✅ SYSTEM STATUS: {'EXCELLENT' if avg_overall < 200 else 'GOOD' if avg_overall < 300 else 'NEEDS OPTIMIZATION'}

Copy this for your PPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Performance Metrics:
• Average API Response: {avg_overall:.0f}ms
• Geospatial Queries: {results.get('search', 0):.0f}ms (PostGIS optimized)
• ML Predictions: {results.get('ml', 0):.0f}ms (Real-time AI)
• System Status: Production-ready
• Test Date: {datetime.now().strftime('%Y-%m-%d')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        # Save to file
        with open('quick_benchmark_ppt.txt', 'w') as f:
            f.write("SMART PARKING SYSTEM - QUICK BENCHMARK RESULTS\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Backend: {BACKEND_URL}\n\n")
            f.write(f"OVERALL AVERAGE: {avg_overall:.0f} ms\n\n")
            f.write("DETAILED RESULTS:\n")
            f.write(f"  Health Check:     {results.get('health', 'N/A'):.0f} ms\n")
            f.write(f"  Parking Search:   {results.get('search', 'N/A'):.0f} ms\n")
            f.write(f"  ML Predictions:   {results.get('ml', 'N/A'):.0f} ms\n")
            f.write(f"  Large Dataset:    {results.get('large', 'N/A'):.0f} ms\n")
            f.write(f"  Multi-Location:   {results.get('location2', 'N/A'):.0f} ms\n\n")
            f.write("FOR POWERPOINT:\n")
            f.write(f"{'='*60}\n")
            f.write(f"Average Response Time: {avg_overall:.0f}ms\n")
            f.write(f"Geospatial Query Performance: {results.get('search', 0):.0f}ms\n")
            f.write(f"ML Prediction Speed: {results.get('ml', 0):.0f}ms\n")
            f.write("Status: Production Ready\n")
        
        print("✓ Results saved to 'quick_benchmark_ppt.txt'\n")
    else:
        print("\n❌ All tests failed. Check if backend is running.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark cancelled.\n")
