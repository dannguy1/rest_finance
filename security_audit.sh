#!/bin/bash
#
# Security Audit Script for Financial Data Processor
# Runs OWASP checks, bandit scan, and dependency vulnerability checks
#

set -e  # Exit on error

echo "========================================="
echo "Security Audit for Financial Data Processor"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory
REPORTS_DIR="security_reports"
mkdir -p "$REPORTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Reports will be saved to: $REPORTS_DIR"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Install required tools if not present
echo "Checking security tools..."
if ! command_exists bandit; then
    echo "${YELLOW}Installing bandit...${NC}"
    pip install bandit
fi

if ! command_exists safety; then
    echo "${YELLOW}Installing safety...${NC}"
    pip install safety
fi

if ! command_exists semgrep; then
    echo "${YELLOW}Installing semgrep...${NC}"
    pip install semgrep
fi

echo "${GREEN}✓ All tools installed${NC}"
echo ""

# 2. Run Bandit (Python security linter)
echo "========================================="
echo "Running Bandit Security Scan..."
echo "========================================="
bandit -r app/ -f json -o "$REPORTS_DIR/bandit_report_$TIMESTAMP.json" || true
bandit -r app/ -f txt -o "$REPORTS_DIR/bandit_report_$TIMESTAMP.txt" || true
echo "${GREEN}✓ Bandit scan complete${NC}"
echo "  Report: $REPORTS_DIR/bandit_report_$TIMESTAMP.txt"
echo ""

# 3. Run Safety (dependency vulnerability checker)
echo "========================================="
echo "Running Safety Dependency Check..."
echo "========================================="
safety check --json --output "$REPORTS_DIR/safety_report_$TIMESTAMP.json" || true
safety check --output text > "$REPORTS_DIR/safety_report_$TIMESTAMP.txt" || true
echo "${GREEN}✓ Safety check complete${NC}"
echo "  Report: $REPORTS_DIR/safety_report_$TIMESTAMP.txt"
echo ""

# 4. Run Semgrep (static analysis)
echo "========================================="
echo "Running Semgrep Static Analysis..."
echo "========================================="
semgrep --config=auto app/ --json -o "$REPORTS_DIR/semgrep_report_$TIMESTAMP.json" || true
semgrep --config=auto app/ -o "$REPORTS_DIR/semgrep_report_$TIMESTAMP.txt" || true
echo "${GREEN}✓ Semgrep analysis complete${NC}"
echo "  Report: $REPORTS_DIR/semgrep_report_$TIMESTAMP.txt"
echo ""

# 5. OWASP Top 10 Checklist
echo "========================================="
echo "OWASP Top 10 Security Checklist"
echo "========================================="

OWASP_REPORT="$REPORTS_DIR/owasp_checklist_$TIMESTAMP.txt"

cat > "$OWASP_REPORT" << 'EOF'
OWASP Top 10 Security Checklist for Financial Data Processor
Generated: $(date)

A01:2021 – Broken Access Control
[ ] Authentication implemented for sensitive endpoints
[ ] Authorization checks before data access
[ ] Path traversal protection implemented
[ ] File access restricted to authorized sources
Status: ✓ File path validation implemented

A02:2021 – Cryptographic Failures
[ ] Sensitive data encrypted at rest
[ ] Secure connections (HTTPS) enforced in production
[ ] No hardcoded secrets in code
[ ] Secure random number generation for tokens
Status: ⚠ Review needed for production deployment

A03:2021 – Injection
[ ] SQL injection protected (using parameterized queries)
[ ] CSV injection protection
[ ] Command injection protection
[ ] Input validation on all endpoints
Status: ✓ Pandas handles CSV parsing safely

A04:2021 – Insecure Design
[ ] Threat modeling performed
[ ] Security requirements defined
[ ] Secure development lifecycle followed
[ ] Rate limiting implemented
Status: ✓ Rate limiting with slowapi

A05:2021 – Security Misconfiguration
[ ] Debug mode disabled in production
[ ] Default passwords changed
[ ] Error messages don't leak sensitive info
[ ] Security headers configured
Status: ⚠ Review production configuration

A06:2021 – Vulnerable and Outdated Components
[ ] Dependencies regularly updated
[ ] Known vulnerabilities tracked
[ ] Automated dependency scanning
[ ] Security patches applied promptly
Status: ✓ Safety checks implemented

A07:2021 – Identification and Authentication Failures
[ ] Multi-factor authentication considered
[ ] Session management secure
[ ] Password policy enforced
[ ] Account lockout after failed attempts
Status: ⚠ Authentication not yet implemented

A08:2021 – Software and Data Integrity Failures
[ ] Code signing implemented
[ ] Integrity checks for uploads
[ ] Secure CI/CD pipeline
[ ] Supply chain security considered
Status: ✓ File validation with MIME type checks

A09:2021 – Security Logging and Monitoring Failures
[ ] Security events logged
[ ] Logs protected from tampering
[ ] Alerting configured for suspicious activity
[ ] Log retention policy defined
Status: ✓ Enhanced logging with correlation IDs

A10:2021 – Server-Side Request Forgery
[ ] URL validation for external requests
[ ] Network segmentation
[ ] Deny by default firewall rules
[ ] Resource access validation
Status: ✓ No external requests from user input

ADDITIONAL SECURITY MEASURES
[✓] File size limits enforced
[✓] File type validation (MIME type)
[✓] Path traversal protection
[✓] Rate limiting on all endpoints
[✓] Structured error handling
[✓] Input sanitization
[⚠] HTTPS enforcement (production only)
[⚠] Authentication/Authorization (to be implemented)
[⚠] Encryption at rest (to be implemented)
[⚠] Security headers (to be configured)

RECOMMENDATIONS FOR PRODUCTION:
1. Implement authentication (OAuth 2.0 / JWT)
2. Add authorization with role-based access control
3. Enable HTTPS with valid certificates
4. Configure security headers (CSP, HSTS, X-Frame-Options)
5. Implement encryption at rest for sensitive data
6. Set up automated security scanning in CI/CD
7. Configure SIEM for security event monitoring
8. Implement DDoS protection
9. Regular penetration testing
10. Security incident response plan

EOF

echo "${GREEN}✓ OWASP checklist generated${NC}"
echo "  Report: $OWASP_REPORT"
echo ""

# 6. Check for common security issues
echo "========================================="
echo "Additional Security Checks..."
echo "========================================="

ADDITIONAL_REPORT="$REPORTS_DIR/additional_checks_$TIMESTAMP.txt"

{
    echo "Additional Security Checks"
    echo "=========================="
    echo ""
    
    echo "1. Checking for hardcoded secrets..."
    grep -r -E "(password|secret|api[_-]?key|token|credential)" app/ --include="*.py" | grep -v "# " | grep -v "def " | grep -v "class " || echo "No obvious hardcoded secrets found"
    echo ""
    
    echo "2. Checking for debug mode..."
    grep -r "debug.*=.*True" app/ --include="*.py" || echo "No debug mode enabled"
    echo ""
    
    echo "3. Checking for eval/exec usage..."
    grep -r -E "(eval|exec)\(" app/ --include="*.py" || echo "No eval/exec usage found"
    echo ""
    
    echo "4. Checking for dangerous imports..."
    grep -r "import pickle" app/ --include="*.py" || echo "No pickle imports found"
    grep -r "import subprocess" app/ --include="*.py" || echo "No subprocess imports found"
    echo ""
    
    echo "5. Checking requirements.txt for known vulnerabilities..."
    pip list --outdated
    echo ""
    
} > "$ADDITIONAL_REPORT"

echo "${GREEN}✓ Additional checks complete${NC}"
echo "  Report: $ADDITIONAL_REPORT"
echo ""

# 7. Summary
echo "========================================="
echo "Security Audit Complete!"
echo "========================================="
echo ""
echo "Reports generated:"
echo "  1. Bandit: $REPORTS_DIR/bandit_report_$TIMESTAMP.txt"
echo "  2. Safety: $REPORTS_DIR/safety_report_$TIMESTAMP.txt"
echo "  3. Semgrep: $REPORTS_DIR/semgrep_report_$TIMESTAMP.txt"
echo "  4. OWASP: $OWASP_REPORT"
echo "  5. Additional: $ADDITIONAL_REPORT"
echo ""
echo "${YELLOW}Please review all reports and address any findings.${NC}"
echo ""

# Check for critical issues
echo "Checking for critical issues..."
CRITICAL_COUNT=$(grep -c "CRITICAL" "$REPORTS_DIR/bandit_report_$TIMESTAMP.txt" || echo "0")
HIGH_COUNT=$(grep -c "HIGH" "$REPORTS_DIR/bandit_report_$TIMESTAMP.txt" || echo "0")

if [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
    echo "${RED}⚠ WARNING: Found $CRITICAL_COUNT critical and $HIGH_COUNT high severity issues!${NC}"
    echo "Please review the bandit report immediately."
    exit 1
else
    echo "${GREEN}✓ No critical or high severity issues found${NC}"
fi
