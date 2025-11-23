#!/usr/bin/env python3
"""
Backend Test Suite for Autonomous Trading Endpoints
Tests the autonomous trading agent endpoints as requested
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://wookie-trader.preview.emergentagent.com/api"

def test_endpoint(method, endpoint, payload=None, expected_status=200):
    """Test a single endpoint and return results"""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {method} {endpoint}")
        print(f"URL: {url}")
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            print(f"Payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response (text): {response.text}")
            response_data = {"raw_text": response.text}
        
        # Check if test passed
        success = response.status_code == expected_status
        
        if success:
            print("✅ TEST PASSED")
        else:
            print(f"❌ TEST FAILED - Expected status {expected_status}, got {response.status_code}")
        
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "success": success,
            "response_data": response_data,
            "error": None
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": str(e)
        }
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": str(e)
        }

def main():
    """Run all autonomous trading endpoint tests - NEUE FEATURES"""
    print("🤖 NEUE AUTONOMOUS TRADING FEATURES TEST SUITE")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    print("\n🎯 TESTING NEW FEATURES:")
    print("   1. Dry-Run Trading Cycle (Simulation)")
    print("   2. Normal Trading Cycle (Consensus Voting)")
    print("   3. Market Status Check")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: GET /api/market/status - Markt-Status prüfen
    print("\n📈 Test 1: Market Status Check")
    result = test_endpoint("GET", "/market/status")
    test_results.append(result)
    
    # Test 2: GET /api/autonomous/status - Status der autonomen Agenten
    print("\n🔍 Test 2: Autonomous Status")
    result = test_endpoint("GET", "/autonomous/status")
    test_results.append(result)
    
    # Test 3: GET /api/autonomous/leaderboard - Performance-Ranking der Agenten
    print("\n🏆 Test 3: Agent Leaderboard")
    result = test_endpoint("GET", "/autonomous/leaderboard")
    test_results.append(result)
    
    # Test 4: GET /api/autonomous/autopilot/status - Autopilot-Konfiguration abrufen
    print("\n🚁 Test 4: Autopilot Status")
    result = test_endpoint("GET", "/autonomous/autopilot/status")
    test_results.append(result)
    
    # Test 5: POST /api/autonomous/autopilot/configure - Autopilot konfigurieren
    print("\n⚙️ Test 5: Configure Autopilot")
    autopilot_config = {
        "enabled": True,
        "interval_minutes": 60
    }
    result = test_endpoint("POST", "/autonomous/autopilot/configure", autopilot_config)
    test_results.append(result)
    
    # Test 6: POST /api/autonomous/start-cycle - DRY-RUN Trading-Zyklus (NEUE FEATURE)
    print("\n🧪 Test 6: DRY-RUN Trading Cycle (Simulation)")
    print("   → Sollte Konsens-Entscheidungen simulieren ohne echte Trades")
    dry_run_payload = {"dry_run": True}
    result = test_endpoint("POST", "/autonomous/start-cycle", dry_run_payload, expected_status=200)
    test_results.append(result)
    
    # Test 7: POST /api/autonomous/start-cycle - NORMALER Trading-Zyklus (NEUE FEATURE)
    print("\n🚀 Test 7: NORMAL Trading Cycle (Consensus Voting)")
    print("   → Sollte gemeinsames Portfolio-Trading mit Agenten-Abstimmung durchführen")
    normal_payload = {"dry_run": False}
    result = test_endpoint("POST", "/autonomous/start-cycle", normal_payload, expected_status=200)
    test_results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    failed_tests = 0
    
    for result in test_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        error_info = f" - {result['error']}" if result["error"] else ""
        print(f"{status} {result['method']} {result['endpoint']}{error_info}")
        
        if result["success"]:
            passed_tests += 1
        else:
            failed_tests += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/len(test_results)*100):.1f}%")
    
    # Detailed analysis
    print("\n" + "=" * 60)
    print("🔍 DETAILED ANALYSIS - NEUE FEATURES")
    print("=" * 60)
    
    for result in test_results:
        if not result["success"]:
            print(f"\n❌ FAILED: {result['method']} {result['endpoint']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
            if result["status_code"]:
                print(f"   Status Code: {result['status_code']}")
            if result["response_data"]:
                print(f"   Response: {json.dumps(result['response_data'], indent=4)}")
        else:
            print(f"\n✅ PASSED: {result['method']} {result['endpoint']}")
            
            # Market Status Analysis
            if result["endpoint"] == "/market/status" and result["response_data"]:
                market_data = result["response_data"]
                is_open = market_data.get("is_open", False)
                print(f"   Market Status: {'OPEN' if is_open else 'CLOSED'}")
                if "timestamp" in market_data:
                    print(f"   Timestamp: {market_data['timestamp']}")
            
            # Leaderboard Analysis
            if result["endpoint"] == "/autonomous/leaderboard" and result["response_data"]:
                if "leaderboard" in result["response_data"]:
                    agents = result["response_data"]["leaderboard"]
                    print(f"   Found {len(agents)} agents in leaderboard")
                    for agent in agents:
                        if isinstance(agent, dict) and "agent" in agent:
                            print(f"   - {agent['agent']}: Rank {agent.get('rank', 'N/A')}")
            
            # Agent Status Analysis
            if result["endpoint"] == "/autonomous/status" and result["response_data"]:
                if "status" in result["response_data"]:
                    status = result["response_data"]["status"]
                    if "agents_status" in status:
                        agents = list(status["agents_status"].keys())
                        print(f"   Active agents: {', '.join(agents)}")
                        print(f"   Mode: {status.get('mode', 'N/A')}")
            
            # DRY-RUN Trading Cycle Analysis (NEUE FEATURE)
            if result["endpoint"] == "/autonomous/start-cycle" and result["response_data"]:
                if "results" in result["response_data"]:
                    cycle_results = result["response_data"]["results"]
                    dry_run = cycle_results.get("dry_run", False)
                    
                    print(f"   🧪 DRY-RUN Mode: {'YES' if dry_run else 'NO'}")
                    print(f"   📊 Trades Proposed: {cycle_results.get('trades_proposed', 0)}")
                    print(f"   ✅ Trades Executed: {cycle_results.get('trades_executed', 0)}")
                    
                    # Konsens-Entscheidungen analysieren
                    if "consensus_decisions" in cycle_results:
                        decisions = cycle_results["consensus_decisions"]
                        print(f"   🗳️  Consensus Decisions: {len(decisions)}")
                        
                        for decision in decisions[:3]:  # Zeige erste 3
                            symbol = decision.get("symbol", "N/A")
                            consensus = decision.get("consensus", "N/A")
                            confidence = decision.get("confidence", 0)
                            executed = decision.get("executed", False)
                            
                            print(f"      - {symbol}: {consensus} (Confidence: {confidence:.2f}, Executed: {executed})")
                            
                            # Agenten-Vorschläge zeigen
                            if "proposals" in decision:
                                proposals = decision["proposals"]
                                print(f"        Agent Votes:")
                                for prop in proposals:
                                    agent = prop.get("agent", "N/A")
                                    action = prop.get("action", "N/A")
                                    conf = prop.get("confidence", 0)
                                    print(f"          {agent}: {action} ({conf:.2f})")
                    
                    print(f"   ⏱️  Timestamp: {cycle_results.get('timestamp', 'N/A')}")
                    
                    # Spezielle Validierung für DRY-RUN
                    if dry_run and cycle_results.get('trades_executed', 0) > 0:
                        print(f"   ⚠️  WARNING: DRY-RUN sollte keine echten Trades ausführen!")
                    elif not dry_run and cycle_results.get('trades_executed', 0) == 0:
                        print(f"   ℹ️  INFO: Normal mode but no trades executed (market closed or no consensus)")
            
            # Autopilot Status Analysis
            if result["endpoint"] == "/autonomous/autopilot/status" and result["response_data"]:
                config = result["response_data"].get("config", {})
                enabled = config.get("enabled", False)
                interval = config.get("interval_minutes", 0)
                print(f"   Autopilot: {'ENABLED' if enabled else 'DISABLED'}")
                if enabled:
                    print(f"   Interval: {interval} minutes")
    
    print(f"\n🏁 Test completed at: {datetime.now()}")
    
    # Return exit code based on results
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)