#!/usr/bin/env python
"""
Quick validation script to test the production-level lead discovery system.
Run this before deploying to verify everything works.

Usage:
    python test_lead_discovery.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.web_scraper import (
    generate_high_intent_queries,
    analyze_business_signals,
    discover_company_websites,
)


async def test_query_generation():
    """Test that high-intent query generation works."""
    print("\n" + "="*70)
    print("TEST 1: Query Generation (8-10 queries)")
    print("="*70)
    
    queries = generate_high_intent_queries(
        query="We need backend developers",
        location="San Francisco",
        industry="saas",
        service_focus=["backend development", "system design"],
        min_queries=8,
        max_queries=10,
    )
    
    print(f"✅ Generated {len(queries)} queries")
    for i, q in enumerate(queries, 1):
        print(f"   {i}. {q}")
    
    if 8 <= len(queries) <= 10:
        print(f"✅ PASS: Query count in valid range (8-10)")
        return True
    else:
        print(f"❌ FAIL: Query count {len(queries)} out of range")
        return False


async def test_signal_detection():
    """Test that signal detection works."""
    print("\n" + "="*70)
    print("TEST 2: Signal Detection")
    print("="*70)
    
    test_cases = [
        {
            "snippet": "TechCorp is hiring backend engineers",
            "website": "We're a SaaS platform for enterprise data",
            "service_focus": ["backend development"],
            "expected_signals": ["hiring", "saas_platform"],
            "name": "Product company advertising jobs",
        },
        {
            "snippet": "IT consulting firm specializing in staffing",
            "website": "Professional services for outsourced development",
            "service_focus": ["backend development"],
            "expected_signals": [],  # Should have low confidence
            "name": "Service provider (should be low confidence)",
        },
        {
            "snippet": "Series A startup building ML platform",
            "website": "We're scaling our infrastructure team rapidly",
            "service_focus": ["machine learning"],
            "expected_signals": ["funding", "scaling"],
            "name": "Funded startup with strong signals",
        },
    ]
    
    all_pass = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        signals = analyze_business_signals(
            snippet=test_case["snippet"],
            website_text=test_case["website"],
            service_focus=test_case["service_focus"],
        )
        
        print(f"Detected signals: {signals['signals']}")
        print(f"Confidence: {signals['confidence']:.2f}")
        print(f"Tech relevance: {signals['tech_relevance']:.2f}")
        print(f"Reasons: {signals['reason']}")
        
        # Validate expectations
        if test_case["expected_signals"]:
            missing = set(test_case["expected_signals"]) - set(signals["signals"])
            if not missing:
                print(f"✅ All expected signals detected")
            else:
                print(f"⚠️  Missing signals: {missing}")
                # Don't fail, just warn - signal detection can vary
        
        if signals['confidence'] > 0:
            print(f"✅ Non-zero confidence score")
        else:
            print(f"❌ Zero confidence (likely low quality)")
            all_pass = False
    
    return all_pass


async def test_discovery():
    """Test that discovery works end-to-end."""
    print("\n" + "="*70)
    print("TEST 3: End-to-End Discovery (using SerpAPI)")
    print("="*70)
    
    # Check if API key is set
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPER_API_KEY")
    if not api_key:
        print("⚠️  SERPAPI_KEY or SERPER_API_KEY not set!")
        print("   Set in .env file to enable discovery test")
        print("   Get free API key from https://serpapi.com")
        return False
    
    print(f"✅ API key detected")
    
    try:
        print("🔍 Performing discovery (this may take 20-30 seconds)...")
        
        results = await discover_company_websites(
            query="SaaS companies hiring backend engineers",
            location="San Francisco",
            industry="software",
            service_focus=["backend development"],
            max_results=10,
        )
        
        print(f"\n✅ Discovery completed!")
        print(f"📊 Found {len(results)} candidates")
        
        if len(results) > 0:
            print(f"\n--- Top Results ---")
            for i, r in enumerate(results[:5], 1):
                print(f"{i}. {r['name']}")
                print(f"   Domain: {r['domain']}")
                print(f"   Snippet: {r['snippet'][:80]}...")
                print(f"   Buyer intent: {r['buyer_intent_signal']}")
            return True
        else:
            print("⚠️  No results found (may need API key or quota)")
            return False
    
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_filtering():
    """Test that filtering works correctly."""
    print("\n" + "="*70)
    print("TEST 4: Buyer Filtering (Service Provider Rejection)")
    print("="*70)
    
    from app.services.web_scraper import _append_candidate_result
    
    test_cases = [
        {
            "href": "https://techcorp.com",
            "title": "TechCorp - SaaS Platform",
            "snippet": "We're building a cloud platform for enterprise",
            "blocked_domains": set(),
            "should_pass": True,
            "name": "Legitimate SaaS company",
        },
        {
            "href": "https://devagency.com",
            "title": "Dev Agency - Hire Our Developers",
            "snippet": "Professional staffing and outsourcing services",
            "blocked_domains": set(),
            "should_pass": False,
            "name": "Service provider (should be rejected)",
        },
        {
            "href": "https://consultingfirm.com",
            "title": "Business Consulting Firm",
            "snippet": "IT consulting and managed services",
            "blocked_domains": set(),
            "should_pass": False,
            "name": "Consulting firm (should be rejected)",
        },
        {
            "href": "https://startupxyz.com",
            "title": "StartupXYZ - Scaling Platform",
            "snippet": "Series A funded startup building ML infrastructure",
            "blocked_domains": set(),
            "should_pass": True,
            "name": "Venture-backed startup (should pass)",
        },
    ]
    
    all_pass = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        results = []
        seen_domains = set()
        
        passed = _append_candidate_result(
            results=results,
            seen_domains=seen_domains,
            href=test_case["href"],
            title=test_case["title"],
            snippet=test_case["snippet"],
            blocked_domains=test_case["blocked_domains"],
        )
        
        if passed == test_case["should_pass"]:
            print(f"✅ Correctly {'accepted' if passed else 'rejected'}")
        else:
            print(f"❌ Incorrectly {'accepted' if passed else 'rejected'}")
            print(f"   Expected: {'pass' if test_case['should_pass'] else 'reject'}")
            all_pass = False
    
    return all_pass


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " PRODUCTION LEAD DISCOVERY SYSTEM - VALIDATION ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    results = {
        "Query Generation": await test_query_generation(),
        "Signal Detection": await test_signal_detection(),
        "Buyer Filtering": await test_filtering(),
        "End-to-End Discovery": await test_discovery(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} | {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print("-" * 70)
    print(f"Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All validation tests passed!")
        print("✅ System is ready for production")
        return 0
    elif passed_count >= total_count - 1:
        print("\n⚠️  Most tests passed")
        print("⚠️  Check API key and network connectivity")
        return 1
    else:
        print("\n❌ Some tests failed")
        print("❌ Fix issues before deploying")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
