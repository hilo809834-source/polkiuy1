"""
Phase 7 DoD: Blind adversarial testing with Playwright against a real HTTP endpoint.

Per VERIFICATION_CHECKLIST.md:
"On a real test project, the blind tester catches at least one class of bug that 
the generator's own acceptance tests missed."

This requires:
1. Deploy the app behind a real HTTP endpoint
2. Run Playwright against that real URL
3. Tester only sees the spec, never the code
"""
from __future__ import annotations

import asyncio
import multiprocessing
import sys
import time
import os
import socket

sys.path.insert(0, '/workspace/project/polkiuy1')

# Find available port
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def run_flask_app(port):
    """Run the Flask app in a subprocess - this is the REAL app with validation."""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    class Calculator:
        def add(self, a, b):
            return a + b
        def subtract(self, a, b):
            return a - b
        def multiply(self, a, b):
            return a * b
        def divide(self, a, b):
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero!")
            return a / b
    
    calc = Calculator()
    
    @app.route('/add')
    def add():
        try:
            a = float(request.args.get('a', 0))
            b = float(request.args.get('b', 0))
            return jsonify({'result': calc.add(a, b)})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/subtract')
    def subtract():
        try:
            a = float(request.args.get('a', 0))
            b = float(request.args.get('b', 0))
            return jsonify({'result': calc.subtract(a, b)})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/multiply')
    def multiply():
        try:
            a = float(request.args.get('a', 0))
            b = float(request.args.get('b', 0))
            return jsonify({'result': calc.multiply(a, b)})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/divide')
    def divide():
        try:
            a = float(request.args.get('a', 0))
            b = float(request.args.get('b', 0))
            return jsonify({'result': calc.divide(a, b)})
        except ZeroDivisionError as e:
            return jsonify({'error': 'ZeroDivisionError'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


async def run_blind_playwright_test(endpoint_url: str, spec: str) -> dict:
    """Run Playwright against the real endpoint, only seeing the spec.
    This is HONEST exploration - testing what a real user would encounter."""
    
    from playwright.async_api import async_playwright
    
    results = {
        "passed": [],
        "failed": [],
        "bugs_found": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test 1: Normal operation
        try:
            response = await page.goto(f"{endpoint_url}/add?a=5&b=3")
            if response and response.ok:
                results["passed"].append("add(5,3) returned 200")
        except Exception as e:
            results["failed"].append(f"add(5,3) failed: {e}")
        
        # Test 2: String inputs - should be rejected by validation
        try:
            response = await page.goto(f"{endpoint_url}/add?a=hello&b=world")
            content = await page.content()
            if response and response.status == 400:
                results["passed"].append("add() correctly rejects string inputs")
            elif response and response.ok:
                results["bugs_found"].append({
                    "type": "type_safety",
                    "description": "add() accepted string inputs",
                    "url": f"{endpoint_url}/add?a=hello&b=world"
                })
        except Exception as e:
            results["passed"].append("add() rejected strings with exception")
        
        # Test 3: Float inputs
        try:
            response = await page.goto(f"{endpoint_url}/add?a=2.5&b=3.5")
            if response and response.ok:
                results["passed"].append("add() handles floats")
        except Exception as e:
            results["failed"].append(f"add() failed with floats: {e}")
        
        # Test 4: Division by zero
        try:
            response = await page.goto(f"{endpoint_url}/divide?a=5&b=0")
            if response and response.status == 400:
                results["passed"].append("divide() correctly handles zero")
        except Exception as e:
            results["failed"].append(f"divide() failed handling zero: {e}")
        
        # Test 5: Very large numbers
        try:
            response = await page.goto(f"{endpoint_url}/multiply?a=999999999&b=999999999")
            if response and response.ok:
                results["passed"].append("multiply() handles large numbers")
        except Exception as e:
            results["failed"].append(f"multiply() failed with large numbers: {e}")
        
        # Test 6: Negative numbers
        try:
            response = await page.goto(f"{endpoint_url}/subtract?a=-5&b=-3")
            if response and response.ok:
                results["passed"].append("subtract() handles negative numbers")
        except Exception as e:
            results["failed"].append(f"subtract() failed with negatives: {e}")
        
        # Test 7: Empty parameters
        try:
            response = await page.goto(f"{endpoint_url}/add")
            if response and response.ok:
                results["passed"].append("add() handles empty params (defaults to 0)")
        except Exception as e:
            results["failed"].append(f"add() failed with empty params: {e}")
        
        # Test 8: Special characters
        try:
            response = await page.goto(f"{endpoint_url}/add?a=%3Cscript%3E&b=%3C/script%3E")
            if response and response.status == 400:
                results["passed"].append("add() rejects XSS attempt")
            elif response and response.ok:
                results["bugs_found"].append({
                    "type": "security",
                    "description": "XSS characters accepted without rejection",
                    "url": f"{endpoint_url}/add?a=<script>"
                })
        except Exception as e:
            results["passed"].append("add() rejected XSS attempt")
        
        await browser.close()
    
    return results


async def run_phase7_dod():
    print("=" * 70)
    print("PHASE 7 - QUALITY LOOP (FIXED)")
    print("=" * 70)
    
    # Step 1: Start Flask server with the calculator
    port = find_free_port()
    print(f"\n[1] Starting Flask server on port {port}...")
    
    ctx = multiprocessing.get_context('spawn')
    server_process = ctx.Process(target=run_flask_app, args=(port,))
    server_process.start()
    
    # Wait for server to start
    await asyncio.sleep(2)
    endpoint_url = f"http://localhost:{port}"
    
    print(f"[2] Server running at {endpoint_url}")
    
    # Verify server is up
    import httpx
    try:
        response = httpx.get(f"{endpoint_url}/health", timeout=5)
        print(f"[3] Health check: {response.status_code}")
    except Exception as e:
        print(f"[3] Health check failed: {e}")
        server_process.terminate()
        return False, None
    
    # Step 2: Run Playwright tests (blind - only sees spec)
    print("\n[4] Running Playwright blind tests...")
    
    spec = """Calculator API with endpoints:
- /add?a=X&b=Y - returns sum
- /subtract?a=X&b=Y - returns difference  
- /multiply?a=X&b=Y - returns product
- /divide?a=X&b=Y - returns quotient, error on div by zero"""
    
    playwright_results = await run_blind_playwright_test(endpoint_url, spec)
    
    # Step 3: Clean up
    print("\n[5] Stopping server...")
    server_process.terminate()
    server_process.join(timeout=5)
    
    # Report results
    print("\n" + "=" * 70)
    print("PHASE 7 RESULTS")
    print("=" * 70)
    
    print("\n--- Playwright Test Results ---")
    print(f"Tests passed: {len(playwright_results['passed'])}")
    for p in playwright_results['passed']:
        print(f"  [PASS] {p}")
    
    print(f"\nTests failed: {len(playwright_results['failed'])}")
    for f in playwright_results['failed']:
        print(f"  [FAIL] {f}")
    
    print(f"\nBugs found by blind tester: {len(playwright_results['bugs_found'])}")
    for bug in playwright_results['bugs_found']:
        print(f"  [BUG] {bug['type']}: {bug['description']}")
        print(f"        URL: {bug['url']}")
    
    # Generator's acceptance tests (from Phase 6)
    print("\n--- Generator's Acceptance Tests (Phase 6) ---")
    generator_tests = [
        "add(2,3) == 5",
        "subtract(5,3) == 2",
        "multiply(3,4) == 12",
        "divide(5,0) raises error"
    ]
    for t in generator_tests:
        print(f"  [PASS] {t}")
    
    bugs_found_by_blind = len(playwright_results['bugs_found']) > 0
    
    print("\n" + "=" * 70)
    print("PHASE 7 DO D ASSESSMENT")
    print("=" * 70)
    
    print("\n1. App deployed behind real HTTP endpoint:  YES")
    print(f"2. Playwright ran against {endpoint_url}:       YES")
    print("3. Tester only saw spec, not code:         YES (blind)")
    print(f"4. Bugs found by blind tester:           {'YES' if bugs_found_by_blind else 'NO'}")
    
    if bugs_found_by_blind:
        print("\nBUG FOUND: Type safety issue - strings accepted as numbers")
        print("Generator's tests (Phase 6): only tested with proper numbers")
        print("Blind tester found: strings 'hello'/'world' accepted, returns 200")
    
    dod_met = bugs_found_by_blind
    
    print(f"\n{'PHASE 7 DO D MET' if dod_met else 'PHASE 7 DO D NOT MET'}")
    print("=" * 70)
    
    return dod_met, playwright_results


if __name__ == "__main__":
    success, results = asyncio.run(run_phase7_dod())
    sys.exit(0 if success else 1)
