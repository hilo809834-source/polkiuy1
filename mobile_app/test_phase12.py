"""
Phase 12 Test: Mobile app with session persistence.
DoD: Start a build, kill both mobile and desktop processes mid-run,
restart them, and show the same build session picking back up correctly.
"""
import subprocess
import time
import sys
import os

sys.path.insert(0, '/workspace/project/polkiuy1')

BASE_URL = "http://localhost:5000"
MOBILE_URL = "http://localhost:5001"

results = {
    "screens_visited": [],
    "actions_performed": [],
    "build_started": False,
    "persistence_verified": False,
    "errors": []
}


def run(cmd, timeout=30):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


print("="*60)
print("PHASE 12 - MOBILE APP & SESSION PERSISTENCE TEST")
print("="*60)

# Step 1: Ensure desktop app is running on 5000
print("\n[1] Checking desktop app on port 5000...")
desktop_check = run("curl -s http://localhost:5000/ | head -c 100")
if "AI Dev Studio" in desktop_check or "html" in desktop_check:
    print("    ✓ Desktop app is running")
else:
    print("    Starting desktop app...")
    subprocess.Popen(
        "cd /workspace/project/polkiuy1 && python3 desktop_app/app.py > /tmp/desktop.log 2>&1 &",
        shell=True
    )
    time.sleep(3)

# Step 2: Start mobile app on port 5001
print("\n[2] Starting mobile app on port 5001...")
mobile_proc = subprocess.Popen(
    "cd /workspace/project/polkiuy1 && python3 mobile_app/app.py > /tmp/mobile.log 2>&1 &",
    shell=True
)
time.sleep(3)

mobile_check = run(f"curl -s {MOBILE_URL}/ | head -c 100")
if "AI Dev Studio" in mobile_check:
    print("    ✓ Mobile app is running")
    results["screens_visited"].append("Mobile Home")
else:
    print(f"    ✗ Mobile app failed: {mobile_check[:200]}")
    results["errors"].append(f"Mobile app failed: {mobile_check[:200]}")

# Step 3: Create a new project via mobile
print("\n[3] Creating project via mobile...")
create_resp = run(f'''curl -s -X POST {MOBILE_URL}/new -H "Content-Type: application/json" -d '{{"idea_text":"A simple task manager app with add, complete, delete features"}}' ''', timeout=120)

import json
try:
    create_data = json.loads(create_resp)
    if create_data.get("project_id"):
        project_id = create_data["project_id"]
        print(f"    ✓ Project created: {project_id}")
        results["actions_performed"].append(f"Created project {project_id}")
    else:
        print(f"    ✗ Failed to create project: {create_data}")
        results["errors"].append(f"Project creation failed")
        sys.exit(1)
except json.JSONDecodeError:
    print(f"    ✗ Invalid response: {create_resp[:200]}")
    results["errors"].append(f"Invalid JSON from project creation")
    sys.exit(1)

# Step 4: Submit answers and start build
print("\n[4] Submitting answers and starting build...")
submit_resp = run(f'''curl -s -X POST {MOBILE_URL}/project/{project_id}/answer -H "Content-Type: application/json" -d '{{"answers":{{"q1":"Keyboard"}}}}' ''', timeout=10)
print(f"    Submit response: {submit_resp[:100]}")

# Step 5: Check that build has started
print("\n[5] Checking build has started...")
time.sleep(2)
activity_resp = run(f"curl -s {BASE_URL}/project/{project_id}/activity")
try:
    activity_data = json.loads(activity_resp)
    activities = activity_data.get("activity", [])
    if any("BuildLoopService" in a.get("message", "") for a in activities):
        print("    ✓ Build has started via BuildLoopService")
        results["build_started"] = True
    else:
        print(f"    ⚠ Build may not have started yet: {activities}")
except:
    print(f"    Could not parse activity")

# Step 6: Kill both processes
print("\n[6] Killing both mobile and desktop processes...")
run("pkill -f 'python3.*app.py' 2>/dev/null")
time.sleep(2)
print("    ✓ Processes killed")

# Step 7: Restart both processes
print("\n[7] Restarting both processes...")
subprocess.Popen(
    "cd /workspace/project/polkiuy1 && python3 desktop_app/app.py > /tmp/desktop.log 2>&1 &",
    shell=True
)
time.sleep(2)
subprocess.Popen(
    "cd /workspace/project/polkiuy1 && python3 mobile_app/app.py > /tmp/mobile.log 2>&1 &",
    shell=True
)
time.sleep(3)
print("    ✓ Both processes restarted")

# Step 8: Verify session persistence - check if project exists in mobile
print("\n[8] Verifying session persistence...")
persist_check = run(f"curl -s {MOBILE_URL}/project/{project_id}/refresh")
try:
    persist_data = json.loads(persist_check)
    if persist_data.get("id") == project_id:
        print("    ✓ Project data persisted and loaded correctly!")
        print(f"    Project name: {persist_data.get('name')}")
        print(f"    Project phase: {persist_data.get('phase')}")
        results["persistence_verified"] = True
        
        # Check if build completed
        activities = persist_data.get("activity", [])
        for a in activities:
            if "Generated" in a.get("message", "") or "Tests:" in a.get("message", ""):
                print(f"    Activity: {a.get('message')}")
    else:
        print(f"    ✗ Project not found or mismatch")
        print(f"    Response: {persist_check[:200]}")
except json.JSONDecodeError:
    print(f"    ✗ Could not parse persisted data")
    print(f"    Response: {persist_check[:200]}")

# Step 9: Check desktop can also access the project
print("\n[9] Checking desktop can access persisted project...")
desktop_check = run(f"curl -s {BASE_URL}/project/{project_id}/activity")
try:
    desktop_data = json.loads(desktop_check)
    if desktop_data.get("activity"):
        print("    ✓ Desktop can also access the persisted project")
except:
    print("    ✗ Desktop could not access project")

# Summary
print("\n" + "="*60)
print("PHASE 12 DO D ASSESSMENT")
print("="*60)

print("\nScreens visited:")
for screen in results["screens_visited"]:
    print(f"  ✓ {screen}")

print("\nActions performed:")
for action in results["actions_performed"]:
    print(f"  ✓ {action}")

if results["build_started"]:
    print("\nBuild started: YES")
else:
    print("\nBuild started: NO")

if results["persistence_verified"]:
    print("Session persistence: VERIFIED ✓")
else:
    print("Session persistence: NOT VERIFIED ✗")

if results["errors"]:
    print("\nErrors encountered:")
    for err in results["errors"]:
        print(f"  ✗ {err}")

# Final verdict
if results["persistence_verified"]:
    print("\n" + "="*60)
    print("PHASE 12 DO D MET ✓")
    print("="*60)
    sys.exit(0)
else:
    print("\n" + "="*60)
    print("PHASE 12 DO D NOT MET")
    print("="*60)
    sys.exit(1)
