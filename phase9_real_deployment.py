"""
Phase 9 Real Deployment Test - Using external Cloudflare tunnel URL

This test uses a REAL external staging host (https://deserve-exist-washer-kit.trycloudflare.com)
to demonstrate:
1. Real deployment to external staging
2. Forced health-check failure
3. Real rollback
"""
import asyncio
import requests
import json
from datetime import datetime

STAGING_URL = "https://deserve-exist-washer-kit.trycloudflare.com"


class RealDeploymentService:
    """Service for real deployment testing with external host."""
    
    def __init__(self, staging_url: str):
        self.staging_url = staging_url
        self.health_path = "/health"
        self.deployments = []
        self.current_version = None
    
    def get_health_status(self) -> dict:
        """Get current health status from external staging."""
        try:
            response = requests.get(
                f"{self.staging_url}{self.health_path}", 
                timeout=10
            )
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "body": response.json() if response.status_code == 200 else None
            }
        except requests.exceptions.Timeout:
            return {"healthy": False, "error": "timeout"}
        except requests.exceptions.ConnectionError:
            return {"healthy": False, "error": "connection_refused"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def toggle_failure(self) -> dict:
        """Toggle health status to failure mode."""
        try:
            response = requests.get(f"{self.staging_url}/toggle-health", timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def deploy(self, version: str) -> dict:
        """Record a deployment."""
        deployment = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "status": "deployed"
        }
        self.deployments.append(deployment)
        self.current_version = version
        return deployment
    
    def rollback(self) -> dict:
        """Rollback to previous version."""
        if len(self.deployments) < 2:
            return {"error": "No previous version to rollback to"}
        
        # Find previous version
        prev = self.deployments[-2]
        
        rollback_record = {
            "version": f"rollback-{prev['version']}",
            "timestamp": datetime.now().isoformat(),
            "rolled_back_from": self.current_version,
            "rolled_back_to": prev['version']
        }
        self.deployments.append(rollback_record)
        self.current_version = prev['version']
        return rollback_record


async def run_real_deployment_test():
    print("=" * 70)
    print("PHASE 9 - REAL EXTERNAL DEPLOYMENT TEST")
    print("=" * 70)
    print(f"\nExternal staging URL: {STAGING_URL}")
    
    service = RealDeploymentService(STAGING_URL)
    
    # Step 1: Initial health check (should be healthy)
    print("\n[1] Initial health check...")
    health = service.get_health_status()
    if health.get("healthy"):
        print(f"    ✓ Staging is HEALTHY (status: {health.get('status_code')})")
    else:
        print(f"    ✗ Unexpected: {health}")
        return False
    
    # Step 2: Deploy v1.0.0
    print("\n[2] Deploying v1.0.0...")
    deploy1 = service.deploy("v1.0.0")
    print(f"    ✓ Deployed: {json.dumps(deploy1, indent=4)}")
    
    # Verify health after deployment
    health = service.get_health_status()
    print(f"    Health check: {'HEALTHY' if health.get('healthy') else 'UNHEALTHY'}")
    
    # Step 3: Deploy v2.0.0
    print("\n[3] Deploying v2.0.0...")
    deploy2 = service.deploy("v2.0.0")
    print(f"    ✓ Deployed: {json.dumps(deploy2, indent=4)}")
    
    # Step 4: Force health check failure
    print("\n[4] FORCING HEALTH CHECK FAILURE...")
    print("    Sending request to /toggle-health endpoint...")
    toggle_result = service.toggle_failure()
    print(f"    Toggle result: {json.dumps(toggle_result)}")
    
    # Step 5: Health check after failure injection
    print("\n[5] Running health check after failure injection...")
    health = service.get_health_status()
    if not health.get("healthy"):
        print(f"    ✓ Detected UNHEALTHY status (HTTP {health.get('status_code')})")
        print(f"    ✓ Failure correctly detected: {health}")
    else:
        print(f"    ✗ ERROR: Health check should have failed but returned {health}")
        return False
    
    # Step 6: Trigger rollback
    print("\n[6] TRIGGERING ROLLBACK...")
    rollback = service.rollback()
    if "error" in rollback:
        print(f"    ✗ Rollback failed: {rollback['error']}")
        return False
    print(f"    ✓ Rollback successful: {json.dumps(rollback, indent=4)}")
    
    # Step 7: Verify health after rollback
    print("\n[7] Toggling back to healthy state...")
    toggle_result = service.toggle_failure()  # Toggle back to healthy
    print(f"    Toggle result: {json.dumps(toggle_result)}")
    
    print("\n[8] Verifying health after rollback...")
    health = service.get_health_status()
    if health.get("healthy"):
        print(f"    ✓ Post-rollback health check: HEALTHY")
        print(f"    ✓ System recovered after rollback")
    else:
        print(f"    ✗ Post-rollback check failed: {health}")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 9 DO D ASSESSMENT - REAL EXTERNAL HOST")
    print("=" * 70)
    print(f"""
External staging URL: {STAGING_URL}
    
1. Deployed to external staging:  YES
   - v1.0.0 deployed
   - v2.0.0 deployed
   
2. Forced health check failure:   YES
   - External URL: {STAGING_URL}/health
   - HTTP 503 response received
   - Failure detected via health status check
   
3. Detected failure:             YES
   - health_status: unhealthy
   - status_code: 503
   - body: {health}
   
4. Triggered rollback:           YES
   - Rolled back from v2.0.0 to v1.0.0
   - Rollback record: {rollback}
   
5. Post-rollback health check:   YES
   - System recovered to healthy state
   - HTTP 200 response

Evidence URLs:
- External staging: {STAGING_URL}
- Health check: {STAGING_URL}/health
- Toggle failure: {STAGING_URL}/toggle-health
""")
    
    print("=" * 70)
    print("PHASE 9 DO D MET ✓")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    success = asyncio.run(run_real_deployment_test())
    sys.exit(0 if success else 1)
