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
    cookie_string = "; ".join([f"{cookie.get('name', '')}={cookie.get('value', '')}" for cookie in cookies if cookie.get('name')])
    
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
    
    # Test different page sizes and collect all incidents
    all_incidents = []
    optimal_page_size = 100  # Start with a reasonable default
    
    # Extended date range - going back to 2018
    print("Testing page sizes and collecting incidents...")
    print("Date range: 2018-01-01 to 2026-12-31")
    print("="*60)
    
    # First, test different page sizes to find the optimal one
    test_sizes = [50, 100, 200, 500, 1000]
    working_sizes = []
    
    for size in test_sizes:
        payload = {
            "url": "/incidents",
            "parameters": {
                "query": {
                    "page": 0, "size": size,
                    "before": "2026-12-31T00:00:00.000Z",
                    "after":  "2018-01-01T00:00:00.000Z",  
                    "sort":   "startsAt","order": "asc"
                }
            }
        }
        try:
            r = requests.get(API_URL,
                           headers=hdrs,
                           params={'passthrough': json.dumps(payload)})
            print(f"Testing size={size:4} → status: {r.status_code}", end="")
            
            if r.status_code == 200:
                try:
                    data = r.json()
                    items = data.get('results', [])
                    total_count = data.get('totalCount', 0)
                    print(f" → got {len(items):3} items (total available: {total_count})")
                    working_sizes.append((size, len(items), total_count))
                    
                    if len(items) == size and total_count > size:
                        print(f"           → Size {size} is working but there are more incidents available")
                    elif len(items) < size:
                        print(f"           → Size {size} got all available incidents")
                    
                except json.JSONDecodeError:
                    print(f" → ERROR: Invalid JSON response")
            else:
                print(f" → ERROR: {r.text[:100]}...")
                
        except Exception as e:
            print(f" → ERROR: {e}")
    
    if not working_sizes:
        print("❌ No working page sizes found! Cannot continue.")
        return
    
    # Choose the largest working page size
    optimal_page_size = max(working_sizes, key=lambda x: x[0])[0]
    total_available = working_sizes[-1][2] if working_sizes else 0
    
    print(f"\n🎯 Using optimal page size: {optimal_page_size}")
    print(f"📊 Total incidents available: {total_available}")
    
    # Now collect all incidents using pagination
    print(f"\n{'='*60}")
    print("COLLECTING ALL INCIDENTS")
    print(f"{'='*60}")
    
    page = 0
    total_collected = 0
    
    while True:
        payload = {
            "url": "/incidents",
            "parameters": {
                "query": {
                    "page": page, 
                    "size": optimal_page_size,
                    "before": "2026-12-31T00:00:00.000Z",
                    "after":  "2018-01-01T00:00:00.000Z",  # Extended to 8+ years
                    "sort":   "startsAt",
                    "order": "asc"  # Changed to ascending to match testing
                }
            }
        }
        
        try:
            print(f"📄 Fetching page {page + 1} (size={optimal_page_size})...", end=" ")
            r = requests.get(API_URL,
                           headers=hdrs,
                           params={'passthrough': json.dumps(payload)})
            
            if r.status_code != 200:
                print(f"❌ Error {r.status_code}: {r.text[:100]}...")
                break
            
            data = r.json()
            items = data.get('results', [])
            
            if not items:
                print("✅ No more incidents found")
                break
            
            # Add incidents to our collection
            all_incidents.extend(items)
            total_collected += len(items)
            
            print(f"✅ Got {len(items)} incidents (total: {total_collected})")
            
            # Show sample incident info from this page
            if items:
                first_incident = items[0]
                print(f"   → Latest in this page: {first_incident.get('createdAt', 'N/A')} - {first_incident.get('description', 'N/A')[:50]}...")
                if len(items) > 1:
                    last_incident = items[-1]
                    print(f"   → Oldest in this page:  {last_incident.get('createdAt', 'N/A')} - {last_incident.get('description', 'N/A')[:50]}...")
            
            # If we got fewer items than the page size, we've reached the end
            if len(items) < optimal_page_size:
                print("✅ Reached end of results (partial page)")
                break
            
            page += 1
            
            # Safety check to prevent infinite loops
            if page > 100:  # Max 100 pages
                print("⚠️  Reached maximum page limit (100 pages)")
                break
                
        except Exception as e:
            print(f"❌ Error on page {page + 1}: {e}")
            break
    
    # Save all incidents to JSON file
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")
    
    if all_incidents:
        output_file = "incidents.json"
        
        # Create a comprehensive data structure
        output_data = {
            "metadata": {
                "total_incidents": len(all_incidents),
                "date_range": {
                    "start": "2018-01-01T00:00:00.000Z",
                    "end": "2026-12-31T00:00:00.000Z"
                },
                "collected_at": "2025-07-02T00:00:00.000Z",
                "page_size_used": optimal_page_size,
                "pages_fetched": page + 1
            },
            "incidents": all_incidents
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully saved {len(all_incidents)} incidents to '{output_file}'")
            print(f"📁 File size: {len(json.dumps(output_data))} characters")
            
            # Show some statistics
            if all_incidents:
                print(f"\n📊 INCIDENT STATISTICS:")
                print(f"   • Total incidents: {len(all_incidents)}")
                
                # Date range of collected incidents
                dates = [inc.get('createdAt') for inc in all_incidents if inc.get('createdAt')]
                if dates:
                    dates.sort()
                    print(f"   • Date range: {dates[0]} to {dates[-1]}")
                
                # Sample incident types or categories if available
                if all_incidents[0]:
                    sample_keys = list(all_incidents[0].keys())
                    print(f"   • Incident data fields: {', '.join(sample_keys[:10])}")
                    if len(sample_keys) > 10:
                        print(f"     ... and {len(sample_keys) - 10} more fields")
            
        except Exception as e:
            print(f"❌ Error saving to file: {e}")
    else:
        print("❌ No incidents collected - nothing to save")

def main():
    print("Hello from get-d4h!")
    capture_headers_and_call()


if __name__ == "__main__":
    capture_headers_and_call()
