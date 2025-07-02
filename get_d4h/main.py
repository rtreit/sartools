from playwright.sync_api import sync_playwright
import json, requests

API_URL = 'https://scvsar.team-manager.us.d4h.com/api/v3'

def capture_headers_and_call():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False for debugging
        context = browser.new_context()
        page = context.new_page()

        # 1. Log in or navigate to your page so that your session/cookies are set:
        print("Navigating to D4H incidents page...")
        page.goto("https://scvsar.team-manager.us.d4h.com/team/incidents")
        
        # Wait for the page to load
        print("Waiting for page to load...")
        page.wait_for_load_state("networkidle")
        
        # Give user time to sign in manually
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("A browser window should have opened.")
        print("Please sign in to D4H in the browser window.")
        print("Once you're signed in and can see the incidents page,")
        print("come back here and press ENTER to continue...")
        print("="*60)
        input("Press ENTER after you've signed in: ")
        
        print("Continuing with API capture...")
        # — (if you need to automate login, you can do page.fill() + page.click() here)

        # 2. Intercept the network request and grab its headers
        captured = {}
        requests_captured = []
        
        def on_request(request):
            print(f"Intercepted request: {request.url}")
            if request.url.startswith(API_URL):
                print(f"Found API request: {request.url}")
                captured['headers'] = request.headers
                captured['url'] = request.url
                # Note: We'll stop listening after we get enough info
            requests_captured.append(request.url)

        page.on("request", on_request)

        # 3. Try to trigger the API call in-page
        print("Attempting to trigger API calls...")
        try:
            page.evaluate("""() => {
                // Try various ways to trigger the API call
                if (window.fetchIncidents) {
                    console.log('Calling window.fetchIncidents');
                    window.fetchIncidents();
                }
                
                // Try to trigger a refresh or reload of data
                if (window.location.reload) {
                    console.log('Reloading page to trigger API calls');
                    // Don't actually reload, just log that we would
                }
                
                // Look for React components and try to trigger updates
                console.log('Page loaded, looking for API calls...');
            }""")
        except Exception as e:
            print(f"JavaScript evaluation error (this is normal after navigation): {e}")
            # Wait a bit for the page to settle after navigation
            page.wait_for_load_state("networkidle")

        # give it more time to fire
        print("Waiting for API calls...")
        page.wait_for_timeout(5000)  # Wait 5 seconds
        
        # Try to trigger any buttons or interactions that might cause API calls
        try:
            # Look for refresh buttons or data loading elements
            page.evaluate("""() => {
                // Try clicking any refresh buttons
                const refreshButtons = document.querySelectorAll('[data-testid*="refresh"], [aria-label*="refresh"], .refresh-button, .reload-button');
                refreshButtons.forEach(btn => {
                    console.log('Found refresh button, clicking:', btn);
                    btn.click();
                });
                
                // Try scrolling to trigger lazy loading
                window.scrollTo(0, document.body.scrollHeight);
            }""")
            page.wait_for_timeout(3000)  # Wait another 3 seconds
        except Exception as e:
            print(f"Error trying to trigger interactions: {e}")
        
        # Give user another chance to interact if needed
        print("\n" + "="*50)
        print("If you need to perform any manual actions")
        print("in the browser to trigger API calls, do so now.")
        print("Press ENTER when ready to finish capture...")
        print("="*50)
        input("Press ENTER to finish: ")
        
        # Extract cookies before closing browser
        cookies = context.cookies()
        
        browser.close()

    print(f"Total requests captured: {len(requests_captured)}")
    print("Sample of captured URLs:")
    for i, url in enumerate(requests_captured[:10]):  # Show first 10 URLs
        print(f"  {i+1}. {url}")
    
    if 'headers' not in captured:
        print("\nFailed to catch the specific API request!")
        print("This might be because:")
        print("1. You need to be logged in first")
        print("2. The API call is triggered by user interaction")
        print("3. The page structure has changed")
        print("4. The API endpoint is different")
        
        # Don't raise an error, just return without making API calls
        return

    print(f"\nSuccessfully captured API request to: {captured['url']}")

    # 4. Extract cookies from the browser context and combine with headers
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    
    hdrs = { k:v for k,v in captured['headers'].items()
             if k.lower() in (
                 'x-d4h-requester','accept','user-agent',
                 'x-csrf-token','referer','authorization'
             )}
    
    # Add the cookies from the browser context
    if cookie_string:
        hdrs['cookie'] = cookie_string
        print(f"Added {len(cookies)} cookies to headers")
    
    print(f"Using headers: {list(hdrs.keys())}")
    
    # Check if we have essential authentication headers
    if 'cookie' not in hdrs:
        print("⚠️  WARNING: No 'cookie' header found - authentication may fail")
    if 'x-d4h-requester' not in hdrs:
        print("⚠️  WARNING: No 'x-d4h-requester' header found - API calls may fail")
    
    # now test different page sizes
    for size in [50,100,150,200]:
        payload = {
            "url": "/incidents",
            "parameters": {
                "query": {
                    "page": 0, "size": size,
                    "before": "2025-07-03T14:00:00.000Z",
                    "after":  "2025-01-01T16:00:00.000Z",
                    "sort":   "startsAt","order": "desc"
                }
            }
        }
        try:
            r = requests.get(API_URL,
                           headers=hdrs,
                           params={'passthrough': json.dumps(payload)})
            print(f"size={size:3} → status: {r.status_code}")
            
            if r.status_code == 200:
                try:
                    # Log the raw response first
                    print(f"          → Raw response (first 500 chars):")
                    print(f"          → {r.text[:500]}")
                    if len(r.text) > 500:
                        print(f"          → ... (truncated, total length: {len(r.text)} chars)")
                    print()
                    
                    data = r.json()
                    items = data.get('results', [])  # Changed from 'incidents' to 'results'
                    print(f"          → Parsed JSON successfully")
                    print(f"          → got {len(items)} items")
                    
                    # Also log the structure of the response
                    if isinstance(data, dict):
                        print(f"          → Response keys: {list(data.keys())}")
                        if 'results' in data and len(data['results']) > 0:
                            print(f"          → First incident keys: {list(data['results'][0].keys())}")
                            # Show a sample incident
                            first_incident = data['results'][0]
                            print(f"          → Sample incident ID: {first_incident.get('id', 'N/A')}")
                            print(f"          → Sample created: {first_incident.get('createdAt', 'N/A')}")
                            print(f"          → Sample description: {first_incident.get('description', 'N/A')[:100]}...")
                    
                except json.JSONDecodeError:
                    print(f"          → response is not JSON (length: {len(r.text)})")
                    print(f"          → response preview: {r.text[:200]}...")
            else:
                print(f"          → error: {r.text[:200]}...")
                
        except Exception as e:
            print(f"size={size:3} → error: {e}")
        print()  # Add spacing between requests

def main():
    print("Hello from get-d4h!")
    capture_headers_and_call()


if __name__ == "__main__":
    capture_headers_and_call()
