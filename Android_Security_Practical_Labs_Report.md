# Android Application Security - Practical Labs Report

## Executive Summary

This report documents the hands-on practical labs conducted as part of the Android Application Security internship program. The labs focused on analyzing vulnerable Android applications, performing runtime attacks, and conducting reverse engineering exercises. All activities were aligned with OWASP Mobile (Android) Security Risks and real-world testing scenarios.

---

## Table of Contents

1. [Lab Environment Setup](#lab-environment-setup)
2. [Lab 1: Android-InsecureBankv2 Analysis](#lab-1-android-insecurebankv2-analysis)
3. [Lab 2: InsecureShop Assessment](#lab-2-insecureshop-assessment)
4. [Lab 3: Runtime Attacks & Protection Bypass](#lab-3-runtime-attacks--protection-bypass)
5. [Lab 4: Reverse Engineering & Debugging](#lab-4-reverse-engineering--debugging)
6. [OWASP Mobile Security Risks Mapping](#owasp-mobile-security-risks-mapping)
7. [Findings and Recommendations](#findings-and-recommendations)
8. [Conclusion](#conclusion)

---

## Lab Environment Setup

### Prerequisites

Before starting the labs, ensure you have the following tools installed:

#### Required Software:
- **Android Studio** (latest version)
- **Android SDK** (API level 28+)
- **Java JDK** (version 8 or 11)
- **ADB (Android Debug Bridge)** - included with Android SDK
- **Frida** - Dynamic instrumentation toolkit
- **GDB (GNU Debugger)** - For debugging
- **APKTool** - For reverse engineering APK files
- **JADX** or **JD-GUI** - Java decompiler
- **Burp Suite** or **OWASP ZAP** - For network traffic analysis
- **Genymotion** or **Android Emulator** - For running vulnerable apps

#### Installation Commands:

```bash
# Install Frida
pip install frida-tools

# Install APKTool (Linux/Mac)
sudo apt-get install apktool  # Ubuntu/Debian
brew install apktool           # macOS

# For Windows, download from: https://ibotpeaches.github.io/Apktool/

# Install JADX
# Download from: https://github.com/skylot/jadx/releases
```

### Setting Up Android Emulator

1. Open Android Studio
2. Go to **Tools → AVD Manager**
3. Click **Create Virtual Device**
4. Select a device (e.g., Pixel 4)
5. Select system image (API 28 or higher, with Google Play)
6. Click **Finish**

### Enabling Developer Options on Android Device/Emulator

1. Go to **Settings → About Phone**
2. Tap **Build Number** 7 times
3. Go back to **Settings → Developer Options**
4. Enable:
   - **USB Debugging**
   - **Install via USB**
   - **Stay Awake**

### Verifying ADB Connection

```bash
# Check if device is connected
adb devices

# Expected output:
# List of devices attached
# emulator-5554    device
```

---

## Lab 1: Android-InsecureBankv2 Analysis

### Objective
Analyze a deliberately vulnerable banking application, identify common Android security flaws, and map findings to OWASP Mobile risks.

### Step-by-Step Instructions

#### Step 1: Download and Build the Application

```bash
# Clone the repository
git clone https://github.com/dineshshetty/Android-InsecureBankv2.git
cd Android-InsecureBankv2

# Open in Android Studio
# File → Open → Select the cloned directory
```

#### Step 2: Build and Install the APK

**Method 1: Using Android Studio**
1. Click **Build → Build Bundle(s) / APK(s) → Build APK(s)**
2. Wait for build to complete
3. Locate the APK in `app/build/outputs/apk/debug/`
4. Install using: `adb install app-debug.apk`

**Method 2: Using Command Line**
```bash
# Navigate to project directory
cd Android-InsecureBankv2

# Build the APK
./gradlew assembleDebug

# Install on connected device/emulator
adb install app/build/outputs/apk/debug/app-debug.apk
```

#### Step 3: Static Analysis

**3.1 Decompile the APK using JADX**

```bash
# Open JADX GUI
jadx-gui app-debug.apk

# Or use command line
jadx -d output_directory app-debug.apk
```

**3.2 Key Areas to Analyze:**

1. **AndroidManifest.xml Analysis**
   - Check exported activities, services, broadcast receivers
   - Review permissions
   - Look for debug flags

2. **Source Code Review**
   - Navigate to: `com/android/insecurebankv2/`
   - Review authentication mechanisms
   - Check for hardcoded credentials
   - Analyze data storage methods

**3.3 Specific Vulnerabilities to Look For:**

```java
// Example: Hardcoded credentials (Check LoginActivity.java)
// Look for strings like:
String username = "dinesh";
String password = "dinesh";

// Example: Insecure data storage (Check SharedPreferences usage)
SharedPreferences prefs = getSharedPreferences("user_prefs", MODE_WORLD_READABLE);

// Example: Insecure communication (Check if HTTPS is properly implemented)
// Review network communication in LoginActivity, DoTransfer, etc.
```

#### Step 4: Dynamic Analysis

**4.1 Intercept Network Traffic**

1. **Configure Burp Suite:**
   - Open Burp Suite
   - Go to **Proxy → Options**
   - Set proxy listener to `127.0.0.1:8080`

2. **Configure Android Emulator to use Burp:**
   ```bash
   # Set proxy on emulator
   adb shell settings put global http_proxy 10.0.2.2:8080
   
   # Install Burp CA certificate
   # In Burp: Proxy → Options → Import/Export CA Certificate
   # Export certificate in DER format
   # Convert to PEM and install on device:
   openssl x509 -inform DER -in burp.der -out burp.pem
   adb push burp.pem /sdcard/
   adb shell
   su
   mv /sdcard/burp.pem /system/etc/security/cacerts/
   chmod 644 /system/etc/security/cacerts/burp.pem
   ```

3. **Capture Traffic:**
   - Launch the InsecureBankv2 app
   - Perform login and other operations
   - Observe traffic in Burp Suite

**4.2 Analyze Logcat Output**

```bash
# Monitor app logs
adb logcat | grep -i "insecurebank"

# Filter for specific tags
adb logcat -s InsecureBankv2:*

# Save logs to file
adb logcat > app_logs.txt
```

**4.3 Check File System Storage**

```bash
# Access app's data directory
adb shell
run-as com.android.insecurebankv2
cd /data/data/com.android.insecurebankv2/
ls -la

# Check shared preferences
cat shared_prefs/*.xml

# Check databases
cd databases/
sqlite3 *.db
.tables
SELECT * FROM users;
```

#### Step 5: Document Findings

Create a findings table:

| Vulnerability | Location | Severity | OWASP Risk | Description |
|--------------|----------|----------|------------|-------------|
| Hardcoded Credentials | LoginActivity.java | High | M1 | Default username/password in source code |
| Insecure Data Storage | SharedPreferences | High | M2 | Sensitive data stored in world-readable files |
| Insecure Communication | Network calls | Medium | M3 | HTTP used instead of HTTPS |
| Weak Cryptography | Encryption methods | Medium | M5 | Weak encryption algorithms used |

---

## Lab 2: InsecureShop Assessment

### Objective
Assess a modern Kotlin-based Android application, identify insecure coding practices and business logic flaws, and understand Kotlin-specific security considerations.

### Step-by-Step Instructions

#### Step 1: Download and Setup

```bash
# Clone the repository
git clone https://github.com/optiv/InsecureShop.git
cd InsecureShop

# Open in Android Studio
# File → Open → Select the cloned directory
```

#### Step 2: Build and Install

```bash
# Build the APK
./gradlew assembleDebug

# Install on device
adb install app/build/outputs/apk/debug/app-debug.apk
```

#### Step 3: Static Analysis

**3.1 Decompile APK**

```bash
jadx-gui app-debug.apk
```

**3.2 Kotlin-Specific Analysis**

Kotlin code may be compiled to Java bytecode. Look for:

1. **Null Safety Issues:**
   ```kotlin
   // Unsafe null handling
   val password: String? = getPassword()
   val length = password.length  // Potential NPE
   ```

2. **Extension Functions:**
   - Review custom extension functions for security issues
   - Check if they expose sensitive operations

3. **Data Classes:**
   - Review data classes for sensitive information exposure
   - Check serialization methods

**3.3 Key Files to Review:**

- `MainActivity.kt` - Entry point
- `LoginActivity.kt` - Authentication logic
- `ProductActivity.kt` - Business logic
- `NetworkService.kt` - API communication
- `DatabaseHelper.kt` - Data storage

#### Step 4: Business Logic Testing

**4.1 Test Authentication Bypass**

1. Launch the app
2. Attempt to access protected activities without authentication:
   ```bash
   # Try to launch protected activity directly
   adb shell am start -n com.optiv.insecureshop/.ProductActivity
   ```

**4.2 Test Authorization Flaws**

1. Login as regular user
2. Attempt to access admin functions
3. Check if client-side authorization can be bypassed

**4.3 Test Input Validation**

1. Enter SQL injection payloads in search fields
2. Test XSS in user input fields
3. Test path traversal in file operations

#### Step 5: Dynamic Analysis with Frida

**5.1 Hook Function Calls**

Create a Frida script (`hook_insecureshop.js`):

```javascript
Java.perform(function() {
    // Hook login function
    var LoginActivity = Java.use("com.optiv.insecureshop.LoginActivity");
    LoginActivity.login.implementation = function(username, password) {
        console.log("[*] Login attempt:");
        console.log("    Username: " + username);
        console.log("    Password: " + password);
        return this.login(username, password);
    };
    
    // Hook API calls
    var NetworkService = Java.use("com.optiv.insecureshop.NetworkService");
    NetworkService.makeRequest.implementation = function(url, data) {
        console.log("[*] API Request:");
        console.log("    URL: " + url);
        console.log("    Data: " + data);
        return this.makeRequest(url, data);
    };
});
```

**5.2 Run Frida Script**

```bash
# Attach Frida to running app
frida -U -f com.optiv.insecureshop -l hook_insecureshop.js --no-pause
```

#### Step 6: Document Findings

| Vulnerability | Type | Severity | Description |
|--------------|------|----------|-------------|
| Business Logic Flaw | Authorization | High | Client-side authorization check can be bypassed |
| SQL Injection | Input Validation | High | User input not sanitized in database queries |
| Insecure API Communication | Network | Medium | API keys exposed in network traffic |

---

## Lab 3: Runtime Attacks & Protection Bypass

### Objective
Learn Frida injection, dynamic instrumentation, root detection bypass, and SSL pinning bypass techniques.

### Part A: Frida Setup and Basic Usage

#### Step 1: Install Frida Server on Android

```bash
# Download Frida server (match your device architecture)
# For ARM64: frida-server-16.x.x-android-arm64.xz
# Extract and push to device

adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"
```

#### Step 2: Verify Frida Connection

```bash
# List running processes
frida-ps -U

# List installed applications
frida-ps -Ua
```

### Part B: Root Detection Bypass

#### Step 1: Identify Root Detection Methods

Common root detection checks:
- `RootBeer` library
- Checking for `su` binary
- Checking for root apps
- Checking for modified system files

#### Step 2: Create Bypass Script

Create `bypass_root.js`:

```javascript
Java.perform(function() {
    console.log("[*] Starting root detection bypass...");
    
    // Bypass RootBeer checks
    var RootBeer = Java.use("com.scottyab.rootbeer.RootBeer");
    RootBeer.isRooted.implementation = function() {
        console.log("[*] RootBeer.isRooted() called - returning false");
        return false;
    };
    
    // Bypass su binary check
    var File = Java.use("java.io.File");
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        if (path.indexOf("su") !== -1 || path.indexOf("Superuser") !== -1) {
            console.log("[*] Blocked su check: " + path);
            return false;
        }
        return this.exists();
    };
    
    // Bypass Runtime.exec checks
    var Runtime = Java.use("java.lang.Runtime");
    Runtime.exec.overload('java.lang.String').implementation = function(command) {
        if (command.indexOf("su") !== -1 || command.indexOf("which su") !== -1) {
            console.log("[*] Blocked command: " + command);
            return null;
        }
        return this.exec(command);
    };
    
    console.log("[*] Root detection bypass installed!");
});
```

#### Step 3: Apply Bypass

```bash
# Attach to app
frida -U -f com.example.app -l bypass_root.js --no-pause
```

### Part C: SSL Pinning Bypass

#### Method 1: Using Frida (Dynamic)

Create `bypass_ssl_pinning.js`:

```javascript
Java.perform(function() {
    console.log("[*] Starting SSL pinning bypass...");
    
    // Bypass OkHttp CertificatePinner
    var CertificatePinner = Java.use("okhttp3.CertificatePinner");
    CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {
        console.log("[*] Bypassed CertificatePinner.check()");
        return;
    };
    
    // Bypass TrustManager
    var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
    var SSLContext = Java.use("javax.net.ssl.SSLContext");
    
    var TrustManager = Java.registerClass({
        name: "com.example.TrustManager",
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() {
                return [];
            }
    }});
    
    // Bypass NetworkSecurityConfig (Android 7+)
    var NetworkSecurityConfig = Java.use("android.security.net.config.NetworkSecurityConfig");
    NetworkSecurityConfig.isCleartextTrafficPermitted.overload('java.lang.String').implementation = function(hostname) {
        console.log("[*] Cleartext traffic permitted for: " + hostname);
        return true;
    };
    
    console.log("[*] SSL pinning bypass installed!");
});
```

#### Method 2: Using Objection (Automated)

```bash
# Install objection
pip install objection

# Launch app with objection
objection -g com.example.app explore

# In objection console:
android sslpinning disable
```

#### Method 3: Static Bypass (Modify APK)

```bash
# Decompile APK
apktool d app.apk -o app_decoded

# Remove SSL pinning code from smali files
# Rebuild APK
apktool b app_decoded -o app_modified.apk

# Sign the APK
keytool -genkey -v -keystore my-release-key.jks -alias my-key -keyalg RSA -keysize 2048 -validity 10000
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore my-release-key.jks app_modified.apk my-key

# Install modified APK
adb install app_modified.apk
```

### Part D: Practical Exercise

**Task:** Bypass root detection and SSL pinning on Android-InsecureBankv2

1. Identify root detection mechanisms
2. Create Frida script to bypass them
3. Identify SSL pinning implementation
4. Bypass SSL pinning using Frida
5. Capture network traffic in Burp Suite
6. Document the process

---

## Lab 4: Reverse Engineering & Debugging

### Objective
Perform static and dynamic reverse engineering of Android applications using ADB and GDB.

### Part A: Static Reverse Engineering

#### Step 1: Extract APK from Device

```bash
# List installed packages
adb shell pm list packages | grep -i bank

# Get package path
adb shell pm path com.android.insecurebankv2

# Pull APK from device
adb pull /data/app/com.android.insecurebankv2-*/base.apk insecurebankv2.apk
```

#### Step 2: Decompile APK

**Using APKTool:**

```bash
# Decompile
apktool d insecurebankv2.apk -o insecurebankv2_decoded

# Analyze structure
cd insecurebankv2_decoded
ls -la

# Key directories:
# - smali/ - Decompiled Dalvik bytecode
# - res/ - Resources
# - AndroidManifest.xml - App manifest
```

**Using JADX:**

```bash
# Decompile to Java source
jadx -d insecurebankv2_java insecurebankv2.apk
```

#### Step 3: Analyze AndroidManifest.xml

```bash
# View manifest
cat AndroidManifest.xml

# Look for:
# - Exported components
# - Permissions
# - Intent filters
# - Debug flags
```

#### Step 4: Analyze Smali Code

```bash
# Navigate to smali directory
cd smali/com/android/insecurebankv2/

# Key files to analyze:
# - LoginActivity.smali - Authentication logic
# - DoTransfer.smali - Transfer functionality
# - ChangePassword.smali - Password change logic

# Search for hardcoded strings
grep -r "password" .
grep -r "http://" .
grep -r "api_key" .
```

### Part B: Dynamic Analysis with ADB

#### Step 1: Monitor App Behavior

```bash
# Monitor logcat
adb logcat -c  # Clear logs
adb logcat | grep -i insecurebank

# Monitor network traffic
adb shell netstat -an | grep ESTABLISHED

# Monitor file system access
adb shell strace -p <PID> -e trace=open,openat
```

#### Step 2: Interact with App Components

```bash
# Launch specific activity
adb shell am start -n com.android.insecurebankv2/.LoginActivity

# Send broadcast
adb shell am broadcast -a com.android.insecurebankv2.CUSTOM_INTENT

# Start service
adb shell am startservice -n com.android.insecurebankv2/.MyService

# Send intent with extras
adb shell am start -a android.intent.action.VIEW \
  -d "insecurebank://transfer?amount=1000&to=attacker" \
  com.android.insecurebankv2
```

#### Step 3: Dump App Memory

```bash
# Get app PID
adb shell pidof com.android.insecurebankv2

# Dump memory (requires root)
adb shell su -c "cat /proc/<PID>/maps > /sdcard/maps.txt"
adb shell su -c "dd if=/proc/<PID>/mem of=/sdcard/memory.dump"

# Pull dumps
adb pull /sdcard/maps.txt .
adb pull /sdcard/memory.dump .
```

#### Step 4: Extract App Data

```bash
# Backup app data (no root required for some apps)
adb backup -f app_backup.ab com.android.insecurebankv2

# Extract backup (requires android-backup-extractor)
java -jar abe.jar unpack app_backup.ab app_backup.tar
tar -xf app_backup.tar

# Access app's data directory (requires root)
adb shell
su
run-as com.android.insecurebankv2
cd /data/data/com.android.insecurebankv2/
ls -la
```

### Part C: Debugging with GDB

#### Step 1: Setup GDB for Android

```bash
# Download GDB server for Android
# Push to device
adb push gdbserver /data/local/tmp/
adb shell chmod 755 /data/local/tmp/gdbserver

# Start app in debug mode
adb shell am start -D -n com.android.insecurebankv2/.LoginActivity

# Get PID
adb shell pidof com.android.insecurebankv2

# Attach GDB server
adb shell /data/local/tmp/gdbserver :1234 --attach <PID>

# Forward port
adb forward tcp:1234 tcp:1234

# Connect with GDB (on host machine)
gdb
(gdb) target remote :1234
(gdb) file app_process  # Load symbols if available
```

#### Step 2: Set Breakpoints and Debug

```gdb
# Set breakpoint at function
(gdb) break Java_com_android_insecurebankv2_LoginActivity_login

# Continue execution
(gdb) continue

# When breakpoint hits:
(gdb) info registers
(gdb) x/10i $pc  # Disassemble current instructions
(gdb) print $r0  # Print register values
(gdb) step       # Step into
(gdb) next       # Step over
(gdb) continue   # Continue execution
```

#### Step 3: Analyze Native Code

```bash
# Extract native libraries
unzip insecurebankv2.apk
cd lib/
file arm64-v8a/libnative.so  # Check architecture

# Analyze with readelf
readelf -h libnative.so
readelf -s libnative.so  # Symbols
readelf -d libnative.so  # Dependencies

# Disassemble with objdump
objdump -d libnative.so > libnative.asm
```

### Part D: Practical Exercise

**Task:** Reverse engineer the authentication mechanism in Android-InsecureBankv2

1. Decompile the APK
2. Locate LoginActivity
3. Identify authentication logic
4. Use ADB to monitor authentication process
5. Use GDB to debug native components (if any)
6. Document the authentication flow
7. Identify vulnerabilities

---

## OWASP Mobile Security Risks Mapping

### OWASP Mobile Top 10 (2016)

| Risk | Description | Lab Coverage |
|------|-------------|--------------|
| **M1: Improper Platform Usage** | Misuse of platform features | Android-InsecureBankv2, InsecureShop |
| **M2: Insecure Data Storage** | Storing sensitive data insecurely | Android-InsecureBankv2 (SharedPreferences) |
| **M3: Insecure Communication** | Weak network security | Both apps (HTTP, SSL pinning bypass) |
| **M4: Insecure Authentication** | Weak authentication mechanisms | Both apps (hardcoded credentials) |
| **M5: Insufficient Cryptography** | Weak encryption | Android-InsecureBankv2 |
| **M6: Insecure Authorization** | Authorization flaws | InsecureShop (client-side checks) |
| **M7: Client Code Quality** | Code-level vulnerabilities | Both apps (static analysis) |
| **M8: Code Tampering** | App modification risks | Runtime attacks (Frida, GDB) |
| **M9: Reverse Engineering** | Code exposure | Reverse engineering labs |
| **M10: Extraneous Functionality** | Hidden features | Static analysis of both apps |

### Detailed Mapping

#### M1: Improper Platform Usage
**Found in:** Android-InsecureBankv2
- **Issue:** Exported activities without proper protection
- **Location:** AndroidManifest.xml
- **Impact:** Unauthorized access to app components

#### M2: Insecure Data Storage
**Found in:** Android-InsecureBankv2
- **Issue:** SharedPreferences with MODE_WORLD_READABLE
- **Location:** LoginActivity.java
- **Impact:** Sensitive user data accessible to other apps

#### M3: Insecure Communication
**Found in:** Both apps
- **Issue:** HTTP used instead of HTTPS, SSL pinning bypass possible
- **Impact:** Man-in-the-middle attacks possible

#### M4: Insecure Authentication
**Found in:** Android-InsecureBankv2
- **Issue:** Hardcoded default credentials
- **Location:** LoginActivity.java
- **Impact:** Unauthorized access with default credentials

---

## Findings and Recommendations

### Critical Findings

1. **Hardcoded Credentials**
   - **Severity:** Critical
   - **Recommendation:** Remove all hardcoded credentials, implement secure authentication

2. **Insecure Data Storage**
   - **Severity:** High
   - **Recommendation:** Use Android Keystore for sensitive data, encrypt before storage

3. **Insecure Communication**
   - **Severity:** High
   - **Recommendation:** Enforce HTTPS, implement certificate pinning properly

### High Findings

4. **Weak Root Detection**
   - **Severity:** High
   - **Recommendation:** Implement multiple root detection methods, server-side validation

5. **SSL Pinning Bypass**
   - **Severity:** High
   - **Recommendation:** Use native SSL pinning, implement certificate pinning in native code

### Medium Findings

6. **Client-Side Authorization**
   - **Severity:** Medium
   - **Recommendation:** Move authorization checks to server-side

7. **Insufficient Input Validation**
   - **Severity:** Medium
   - **Recommendation:** Implement comprehensive input validation and sanitization

### Best Practices Recommendations

1. **Security by Design**
   - Implement security from the initial design phase
   - Follow secure coding guidelines
   - Regular security code reviews

2. **Defense in Depth**
   - Implement multiple layers of security
   - Don't rely on single security controls
   - Server-side validation is essential

3. **Regular Security Testing**
   - Conduct regular penetration testing
   - Use automated security scanning tools
   - Perform code reviews

4. **Secure Development Lifecycle**
   - Integrate security into CI/CD pipeline
   - Use static and dynamic analysis tools
   - Regular dependency updates

---

## Conclusion

The practical labs provided hands-on experience with Android application security testing, covering:

1. **Static Analysis:** Decompiling and analyzing APK files to identify vulnerabilities
2. **Dynamic Analysis:** Runtime testing using Frida, ADB, and network interceptors
3. **Reverse Engineering:** Understanding app internals through debugging and code analysis
4. **Protection Bypass:** Techniques to bypass root detection and SSL pinning

### Key Learnings

- Understanding OWASP Mobile Security Risks in practice
- Hands-on experience with industry-standard tools (Frida, ADB, GDB, APKTool)
- Real-world vulnerability identification and exploitation
- Importance of defense-in-depth security measures

### Future Work

- Advanced obfuscation techniques
- Native code analysis
- Automated security testing frameworks
- Mobile app security automation

---

## Appendix

### Useful Commands Reference

```bash
# ADB Commands
adb devices                    # List connected devices
adb install app.apk           # Install APK
adb uninstall com.package     # Uninstall app
adb shell pm list packages    # List installed packages
adb logcat                     # View logs
adb shell dumpsys package <package>  # Package info

# Frida Commands
frida-ps -U                   # List processes
frida -U -f <package> -l script.js  # Attach with script
frida -U <package> -l script.js     # Attach to running app

# APKTool Commands
apktool d app.apk            # Decompile
apktool b app_decoded        # Rebuild
apktool if framework.apk     # Install framework

# JADX Commands
jadx app.apk                 # Decompile to current directory
jadx -d output app.apk       # Decompile to output directory
jadx-gui app.apk             # Open GUI
```

### Resources

- **OWASP Mobile Security:** https://owasp.org/www-project-mobile-security/
- **Frida Documentation:** https://frida.re/docs/
- **APKTool Documentation:** https://ibotpeaches.github.io/Apktool/
- **Android Security Guidelines:** https://developer.android.com/training/articles/security-tips

---

**Report Prepared By:** [Your Name]  
**Date:** [Current Date]  
**Internship Program:** Android Application Security  
**Organization:** [Organization Name]

