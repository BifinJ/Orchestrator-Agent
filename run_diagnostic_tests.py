# run_diagnostic_tests.py

"""
Quick script to run all diagnostic tests and generate reports.
"""

import os
import sys
from pathlib import Path

# Create reports directory if it doesn't exist
Path("reports").mkdir(exist_ok=True)

print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         DIAGNOSTIC SYSTEM COMPREHENSIVE TEST SUITE                 ║
║                                                                    ║
║  • 200 test cases across 20 categories                            ║
║  • Accuracy, latency, and confidence metrics                      ║
║  • LLM fallback performance analysis                              ║
║  • Beautiful HTML report with charts                              ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")

print("Setting up test environment...")

# Import test suite
try:
    from tests.test_diagnostic_system import DiagnosticTestSuite, run_test_suite
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    print("\nMake sure you're running from the project root directory.")
    sys.exit(1)

print("✓ Test modules loaded successfully\n")

# Ask user if they want to run tests
print("This test suite will:")
print("  1. Run 200 diagnostic test cases")
print("  2. Measure accuracy and performance")
print("  3. Generate detailed JSON report")
print("  4. Create interactive HTML report\n")

response = input("Ready to start? (yes/no): ").strip().lower()

if response not in ['yes', 'y']:
    print("Test cancelled.")
    sys.exit(0)

print("\n" + "=" * 70)
print("STARTING COMPREHENSIVE TEST SUITE")
print("=" * 70 + "\n")

# Run tests
try:
    suite, report = run_test_suite()
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    print("\n📊 QUICK SUMMARY:")
    print(f"   Total Tests:    {report['summary']['total_tests']}")
    print(f"   Passed:         {report['summary']['passed']}")
    print(f"   Failed:         {report['summary']['failed']}")
    print(f"   Accuracy:       {report['summary']['accuracy_percent']}%")
    print(f"   Avg Latency:    {report['summary']['avg_latency_ms']}ms")
    print(f"   LLM Usage:      {report['summary']['llm_usage_rate_percent']}%")
    
    print("\n📁 REPORTS GENERATED:")
    print("   • reports/diagnostic_test_report.json (detailed JSON)")
    print("   • reports/diagnostic_test_results_detailed.json (all test cases)")
    print("   • reports/diagnostic_report.html (interactive report)")
    
    print("\n🌐 VIEW REPORT:")
    print(f"   Open 'reports/diagnostic_report.html' in your browser")
    
    # Performance verdict
    accuracy = report['summary']['accuracy_percent']
    print("\n🎯 PERFORMANCE VERDICT:")
    if accuracy >= 90:
        print("   ✅ EXCELLENT - System performing at production level!")
    elif accuracy >= 80:
        print("   ✓ GOOD - System ready for deployment with minor tuning")
    elif accuracy >= 70:
        print("   ⚠️  ACCEPTABLE - System needs improvement before production")
    else:
        print("   ❌ NEEDS WORK - Significant improvements required")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if report['summary']['llm_usage_rate_percent'] > 20:
        print("   • High LLM usage detected - consider adding more rule patterns")
    if report['summary']['avg_latency_ms'] > 200:
        print("   • Average latency high - optimize diagnostic rules")
    if report['failure_analysis']['failure_reasons']['wrong_root_cause'] > 10:
        print("   • Multiple wrong diagnoses - review dependency graph")
    if accuracy >= 90 and report['summary']['avg_latency_ms'] < 150:
        print("   ✓ System is well-tuned and production-ready!")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"\n❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


if __name__ == "__main__":
    pass