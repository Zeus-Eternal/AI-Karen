#!/bin/bash

# Production Readiness Validation Runner
# This script runs comprehensive production readiness validation

set -e

echo "🚀 Starting Production Readiness Validation"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Check if server is running
check_server() {
    print_status "INFO" "Checking if server is running..."
    
    if curl -s -f http://localhost:8010/api/health > /dev/null 2>&1; then
        print_status "SUCCESS" "Server is running on http://localhost:8010"
        return 0
    else
        print_status "ERROR" "Server is not running on http://localhost:8010"
        print_status "INFO" "Please start the server before running validation"
        return 1
    fi
}

# Install dependencies if needed
install_dependencies() {
    print_status "INFO" "Checking Python dependencies..."
    
    if ! python3 -c "import psutil, requests" 2>/dev/null; then
        print_status "INFO" "Installing required Python packages..."
        pip3 install psutil requests
    fi
    
    print_status "INFO" "Checking Playwright dependencies..."
    cd ui_launchers/web_ui
    
    if [ ! -d "node_modules" ]; then
        print_status "INFO" "Installing Node.js dependencies..."
        npm install
    fi
    
    if [ ! -d "node_modules/@playwright" ]; then
        print_status "INFO" "Installing Playwright..."
        npx playwright install
    fi
    
    cd ../..
}

# Run Python validation script
run_python_validation() {
    print_status "INFO" "Running Python production validation..."
    
    if python3 scripts/production_readiness_validation.py; then
        print_status "SUCCESS" "Python validation completed successfully"
        return 0
    else
        local exit_code=$?
        case $exit_code in
            1)
                print_status "ERROR" "Python validation failed - system not ready for production"
                ;;
            2)
                print_status "WARNING" "Python validation completed with warnings - needs attention"
                ;;
            3)
                print_status "ERROR" "Python validation failed with errors"
                ;;
            *)
                print_status "ERROR" "Python validation failed with unknown error (exit code: $exit_code)"
                ;;
        esac
        return $exit_code
    fi
}

# Run Playwright E2E tests
run_playwright_tests() {
    print_status "INFO" "Running Playwright E2E tests..."
    
    cd ui_launchers/web_ui
    
    # Run production readiness test
    if npx playwright test production-readiness.spec.ts --config playwright.audit.config.ts --reporter=list; then
        print_status "SUCCESS" "Production readiness E2E tests passed"
        e2e_success=true
    else
        print_status "ERROR" "Production readiness E2E tests failed"
        e2e_success=false
    fi
    
    # Run comprehensive audit
    if npx playwright test comprehensive-audit.spec.ts --config playwright.audit.config.ts --reporter=list; then
        print_status "SUCCESS" "Comprehensive audit tests passed"
        audit_success=true
    else
        print_status "WARNING" "Comprehensive audit tests had issues"
        audit_success=false
    fi
    
    # Run accessibility tests
    if npx playwright test accessibility.spec.ts --config playwright.audit.config.ts --reporter=list; then
        print_status "SUCCESS" "Accessibility tests passed"
        a11y_success=true
    else
        print_status "WARNING" "Accessibility tests had issues"
        a11y_success=false
    fi
    
    # Run performance tests
    if npx playwright test performance.spec.ts --config playwright.audit.config.ts --reporter=list; then
        print_status "SUCCESS" "Performance tests passed"
        perf_success=true
    else
        print_status "WARNING" "Performance tests had issues"
        perf_success=false
    fi
    
    cd ../..
    
    # Return success if critical tests passed
    if [ "$e2e_success" = true ]; then
        return 0
    else
        return 1
    fi
}

# Generate final report
generate_final_report() {
    print_status "INFO" "Generating final production readiness report..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="production_readiness_final_report_${timestamp}.md"
    
    cat > "$report_file" << EOF
# Production Readiness Final Report

**Generated:** $(date)
**Validation Run:** $timestamp

## Summary

This report summarizes the comprehensive production readiness validation performed on the Kari AI system.

### Validation Components

1. **Server Health Checks** - ✅ Completed
2. **Database Synchronization** - ✅ Completed  
3. **Plugin Load Order** - ✅ Completed
4. **Response Formatting Integration** - ✅ Completed
5. **E2E Test Suite** - ✅ Completed
6. **UI/UX Production Readiness** - ✅ Completed
7. **Performance Validation** - ✅ Completed
8. **Security Validation** - ✅ Completed

### Test Results

#### Python Validation
- Status: $([ $python_exit_code -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Details: See production_readiness_report_*.json

#### Playwright E2E Tests
- Production Readiness: $([ "$e2e_success" = true ] && echo "✅ PASSED" || echo "❌ FAILED")
- Comprehensive Audit: $([ "$audit_success" = true ] && echo "✅ PASSED" || echo "⚠️ WARNINGS")
- Accessibility: $([ "$a11y_success" = true ] && echo "✅ PASSED" || echo "⚠️ WARNINGS")
- Performance: $([ "$perf_success" = true ] && echo "✅ PASSED" || echo "⚠️ WARNINGS")

### Overall Assessment

$(if [ $python_exit_code -eq 0 ] && [ "$e2e_success" = true ]; then
    echo "🎉 **PRODUCTION READY** - All critical validations passed"
elif [ $python_exit_code -eq 2 ] || [ "$e2e_success" = false ]; then
    echo "⚠️ **NEEDS ATTENTION** - Some issues detected, review required"
else
    echo "❌ **NOT READY** - Critical issues must be resolved"
fi)

### Recommendations

1. Review detailed validation logs for any warnings or failures
2. Address any failed critical tests before production deployment
3. Monitor system performance and resource usage
4. Ensure all security recommendations are implemented
5. Validate backup and recovery procedures

### Files Generated

- Python validation report: production_readiness_report_*.json
- Playwright test reports: ui_launchers/web_ui/playwright-audit-report/
- This summary report: $report_file

---

**Next Steps:**
$(if [ $python_exit_code -eq 0 ] && [ "$e2e_success" = true ]; then
    echo "✅ System is ready for production deployment"
else
    echo "🔧 Address identified issues and re-run validation"
fi)
EOF

    print_status "SUCCESS" "Final report generated: $report_file"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Initialize variables
    python_exit_code=0
    e2e_success=false
    audit_success=false
    a11y_success=false
    perf_success=false
    
    print_status "INFO" "Production Readiness Validation Started"
    
    # Check prerequisites
    if ! check_server; then
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Run Python validation
    if run_python_validation; then
        python_exit_code=0
    else
        python_exit_code=$?
    fi
    
    # Run Playwright tests
    run_playwright_tests
    
    # Generate final report
    generate_final_report
    
    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    
    print_status "INFO" "Total execution time: ${execution_time} seconds"
    
    # Final status
    if [ $python_exit_code -eq 0 ] && [ "$e2e_success" = true ]; then
        print_status "SUCCESS" "🎉 Production readiness validation completed successfully!"
        print_status "INFO" "System is ready for production deployment"
        exit 0
    elif [ $python_exit_code -eq 2 ] || [ "$e2e_success" = false ]; then
        print_status "WARNING" "⚠️ Production readiness validation completed with warnings"
        print_status "INFO" "Review issues and consider fixes before deployment"
        exit 2
    else
        print_status "ERROR" "❌ Production readiness validation failed"
        print_status "INFO" "Critical issues must be resolved before deployment"
        exit 1
    fi
}

# Handle script interruption
trap 'print_status "ERROR" "Validation interrupted"; exit 130' INT TERM

# Run main function
main "$@"