# Day-2: OWASP ZAP DAST Scan Implementation
This README provides a detailed walkthrough of the implementation of a Dynamic Application Security Testing (DAST) scan using OWASP ZAP, integrated into a GitHub Actions CI/CD pipeline. Below, you'll find an explanation of the process, the CI configuration, the vulnerabilities identified, and the recommended fixes to enhance the security of the Flask application.

---

## Project Overview

This project demonstrates the integration of OWASP ZAP (Zed Attack Proxy) into a CI/CD pipeline to perform automated security scans on a Flask web application hosted locally during the build process. The goal is to identify vulnerabilities, align them with the OWASP Top 10, and propose actionable fixes to secure the application.

- **Application**: A simple Flask app located in `Day-2/app/`.
- **Security Tool**: OWASP ZAP for DAST scanning.
- **CI/CD Platform**: GitHub Actions.
- **Objective**: Detect and mitigate security issues, submitting findings for review.

---

## 🛠️ Implementation Steps

### 1. Setting Up the Environment
The journey began by setting up a Python 3.9 environment using `actions/setup-python@v5` to ensure compatibility with the Flask app's dependencies.

### 2. Installing Dependencies
Dependencies listed in `Day-2/app/requirements.txt` were installed using `pip`. This step ensures the Flask app runs smoothly with all required packages.

### 3. Running the Flask Application
The Flask app (`app.py`) was launched in the background using `python3 app.py &`. A custom health check with `curl` and a 30-second timeout (with 3-second intervals) ensured the app was responsive at `http://localhost:5000` before the scan.

### 4. Installing ZAP Dependencies
The `default-jre` package was installed via `apt-get` to support OWASP ZAP, which requires a Java runtime environment.

### 5. Running the ZAP Scan
The ZAP baseline scan was executed using a Docker container (`ghcr.io/zaproxy/zaproxy:stable`) with the following configuration:
- **Target**: `http://localhost:5000`.
- **Options**: Generated HTML (`-r report_html.html`), JSON (`-J report_json.json`), and Markdown (`-w report_md.md`) reports.
- **Ignore Warnings**: Exit code 2 (warnings) was ignored with `|| true` to allow completion.
- The scan ran in the `zap-workspace` directory with root user privileges for proper file access.

### 6. Preparing and Verifying Reports
Reports were moved from `zap-workspace` to `zap-reports/`, with a fallback check in the root directory. The "Verify reports" step ensured at least one report (HTML or JSON) was generated, providing debug output if missing.

### 7. Uploading Artifacts
The `zap-reports/` and `zap-workspace/` directories were uploaded as artifacts using `actions/upload-artifact@v4`, retaining them for 30 days for review.

### 8. Displaying Summary
A summary was added to the GitHub Actions summary page, highlighting 59 passed checks, 8 warnings, and 0 failures, with a note on the expected exit code 2 behavior.

---

## CI/CD Configuration (`.github/workflows/owasp-zap.yml`)

The YAML file orchestrates the entire process. Here’s a breakdown of each component:

- **`name`**: "Day-2 OWASP ZAP DAST Scan" – Names the workflow for easy identification.
- **`on`**: Triggers on `push` or `pull_request` to the `main` branch, limited to changes in `Day-2/**`.
- **`jobs.zap-scan`**: Defines the job running on `ubuntu-latest`.
- **`steps`**:
  1. **Checkout code**: Uses `actions/checkout@v4` to fetch the repository.
  2. **Set up Python**: Configures Python 3.9 for the environment.
  3. **Install dependencies**: Runs `pip install` in the app directory.
  4. **Run Flask app**: Starts the app and waits for it to be ready.
  5. **Install ZAP dependencies**: Sets up Java runtime.
  6. **Run ZAP Scan**: Executes the baseline scan with Docker.
  7. **Prepare reports**: Organizes reports into `zap-reports/`.
  8. **Verify reports**: Checks for report generation.
  9. **Upload ZAP Reports**: Stores artifacts.
  10. **Display Scan Summary**: Adds a summary to the Actions tab.

This configuration ensures a seamless, automated security scan integrated into the CI pipeline.

---

## Screenshots
This section contains visual evidence of the setup, execution, and findings from the ZAP scan and CI/CD pipeline.

- ![ZAP Report Screenshot:](Day-2/app/screenshot/Zap-report.png)

- ![GitHub Actions Workflow Run:](Day-2/app/screenshot/Green-CI.png)

- ![Local SQLi Test Screenshot:](Day-2/app/screenshot/Flask-running-app.png)

- ![CI Artifact Download:](Day-2/app/screenshot/CI-report-with-artifact.png)

---

## Analysis of ZAP Scan Report - OWASP Top 10 Vulnerabilities

The ZAP scan identified 8 warnings, which have been mapped to OWASP Top 10 categories. Below are the detailed findings based on the scan and local testing.

### Vulnerability 1: Missing Security Headers (Related to A05:2021-Security Misconfiguration)
- **OWASP Top 10 Category**: A05:2021 - Security Misconfiguration

#### Vulnerabilities Identified:
- **Content Security Policy (CSP) Header Not Set** (Medium Risk)
- **Missing Anti-clickjacking Header** (Medium Risk)
- **X-Content-Type-Options Header Missing** (Low Risk)
- **Permissions Policy Header Not Set** (Low Risk)

#### Impact:
- **Cross-Site Scripting (XSS) Attacks**: Without CSP, attackers can inject malicious scripts that steal session cookies, redirect users to phishing sites, or deface the application.
- **Clickjacking Attacks**: Missing anti-clickjacking headers allow attackers to embed the site in invisible frames, tricking users into unintended actions.
- **MIME Sniffing Attacks**: Missing `X-Content-Type-Options` can lead to browsers misinterpreting content, potentially executing malicious files.
- **Unauthorized Feature Access**: Without `Permissions-Policy`, sensitive features like camera or microphone might be accessed without consent.

#### Real-World Attack Scenario:
An attacker could create a malicious website embedding the login page in an invisible iframe. Users visiting the attacker’s site might unknowingly enter credentials, which the attacker captures.

#### Suggested Fixes:
```python
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)

# Configure security headers
csp = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:"
}

talisman = Talisman(
    app,
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src'],
    force_https=False,  # Set to True in production
    frame_options='DENY',
    frame_options_allow_from=None,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    strict_transport_security_include_subdomains=True,
    strict_transport_security_preload=True,
    x_content_type_options=True,
    x_xss_protection=True
)

# Manual header setup (alternative)
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Permissions-Policy'] = "camera=(), microphone=(), geolocation=()"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### Vulnerability 2: Non-Storable Content (Related to A06:2021-Vulnerable and Outdated Components)
- **OWASP Top 10 Category**: A06:2021 - Vulnerable and Outdated Components

#### Vulnerabilities Identified:
- **Non-Storable Content [10049]** (Low Risk)

#### Impact:
- **Cache Exploitation**: The `Non-Storable Content` warning indicates that some responses (e.g., redirects or dynamic pages) lack proper cache-control headers, allowing them to be stored in browser caches or intermediary proxies. Attackers could exploit cached sensitive data (like login pages) if not handled correctly.
- **Data Leakage**: If sensitive pages are cached unintentionally, users on shared devices or networks might access outdated or private information.
- **Performance Issues**: Improper caching can lead to inconsistent user experiences or increased server load.

#### Real-World Attack Scenario:
An attacker could access a cached version of the `/login` page from a public Wi-Fi cache, potentially retrieving a user’s session data if the page wasn’t properly marked as non-cacheable.

#### Suggested Fixes:
```python
from flask import Flask, after_this_request, make_response

app = Flask(__name__)

@app.route('/')
def index():
    @after_this_request
    def add_cache_headers(response):
        # Prevent caching of sensitive pages
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return make_response("Welcome to the app!")

# Apply globally if needed
@app.after_request
def apply_cache_control(response):
    if 'login' in request.path or 'sensitive' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response
```

## Core Concept Questions

###1. What is the purpose of DAST and how does it complement other security testing methods?

Purpose of DAST: DAST, or Dynamic Application Security Testing, is like a security guard that checks your app while it’s running. It scans the app from the outside (like a hacker would) to find vulnerabilities such as missing security settings or weak spots that could be attacked. Unlike checking the code directly, DAST looks at how the app behaves in real-time.
Complementing Other Methods: DAST works alongside other tests like Static Application Security Testing (SAST), which checks the code before it runs, and Software Composition Analysis (SCA), which looks at third-party libraries. Together, they cover all angles—SAST finds issues in the code, SCA spots library risks, and DAST catches runtime problems. This teamwork ensures a stronger, more secure app!

### 2. Explain how XSS or SQL injection vulnerabilities can affect an application and its users.

**XSS (Cross-Site Scripting):** This happens when an attacker sneaks malicious scripts (like JavaScript) into your app, often through user input (e.g., a search bar). If not stopped, it can steal users’ cookies (which hold login info), redirect them to fake websites to steal data, or mess up the app’s look. For users, this means their personal info (like passwords) could be stolen, and they might not even know!

**SQL Injection:** This occurs when an attacker adds harmful SQL code (e.g., via a login form) to trick the app into revealing or changing data in the database. It can expose all user data, delete records, or even let the attacker take over the app. Users might lose their accounts, and the app’s data could be wiped out or sold on the dark web.

### 3. Describe the steps you would take to fix the vulnerabilities detected in your ZAP scan.

**Step 1:** Add Security Headers

Use tools like flask_talisman or manually add headers (e.g., Content-Security-Policy, X-Frame-Options) to block XSS and clickjacking. This tells browsers how to protect the app.


**Step 2:** Hide Server Info

Change or remove the Server header (e.g., using a custom WSGI app) to hide version details like Werkzeug/3.1.3, making it harder for attackers to target specific flaws.


**Step 3:** Fix Authentication

Add rate limiting (e.g., with flask_limiter) to stop brute force attacks on /login, and add delays for failed attempts to slow attackers down.


**Step 4:** Patch Local Vulnerabilities

For XSS, use markupsafe.escape() to clean user input on /search. For SQLi, switch to parameterized queries in database calls to prevent code injection.


**Step 5:** Test and Deploy

Re-run the ZAP scan to confirm fixes work, then update the app in production.



### 4. How does integrating ZAP scans into CI/CD pipelines support shift-left security practices?

**What is Shift-Left?:** Shift-left means moving security checks to the beginning of the development process, not just at the end. It’s like fixing a leaky pipe as soon as you see a drip, not after the house floods!

**How ZAP Helps:** By adding ZAP scans to the CI/CD pipeline (e.g., on every push to main), we catch security issues early—while coding or testing—rather than after deployment. This saves time and money, as fixing bugs later is harder and costlier.

**Benefits:** Developers get instant feedback (e.g., 8 warnings in our scan), can fix problems before release, and build a habit of secure coding. It’s like having a safety net that catches issues before they reach users!


## Challenges and Solutions

#### **Challenge 1:** Report Generation Failure

**Issue:** Multiple -r options caused the report to be written to report_html.html inside the container.

**Solution:** Removed custom cmd_options and copied the default report manually.

#### **Challenge 2:** GitHub API 403 Error

**Issue:** The action attempted to create issues but lacked permissions.

**Solution:** Added ZAP_DISABLE_GITHUB_ISSUES (or adjusted repo permissions to allow issue creation).

#### **Challenge 3:** ZAP Artifact Upload Failure

**Issue:** ZAP action failed with "Create Artifact Container failed: The artifact name zap_scan is not valid" due to internal artifact upload conflicts.

**Solution:** Added upload_artifacts: false and allow_issue_writing: false parameters to disable ZAP's internal upload mechanism and handled artifact upload manually using GitHub's upload-artifact action.

#### **Challenge 4:** Docker Permission Errors

**Issue:** ZAP Docker container couldn't write reports due to permission denied errors when mounting volumes.

**Solution:** Used -u root flag in Docker command and created separate workspace directories with proper permissions (chmod 755) for report generation.

#### **Challenge 5:** ZAP Exit Code 2 (Warnings)

**Issue:** ZAP baseline scan exits with code 2 when warnings are found, causing CI/CD pipeline to fail.

**Solution:** Added || true to the ZAP command to ignore warning exit codes and implemented proper error handling to continue workflow execution while still generating reports.