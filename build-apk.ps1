# KATSU Android APK Builder
# Builds, optimizes, zipaligns, and signs the standalone KATSU Android APK.

param(
    [string]$OutputApk = "KATSU-v1.0.apk",
    [string]$Keystore = "android\katsu.keystore",
    [string]$KeyPass = "katsu123",
    [string]$KeyAlias = "katsu"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "       KATSU Android APK Builder         " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Environment Detection
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
if (-not (Test-Path $sdk)) {
    throw "Android SDK not found at $sdk"
}

# Locate build-tools
$buildToolsDirs = Get-ChildItem "$sdk\build-tools" | Sort-Object Name -Descending
if ($buildToolsDirs.Count -eq 0) {
    throw "No Android build-tools found in $sdk\build-tools"
}
$buildTools = $buildToolsDirs[0].FullName
Write-Host "[+] Using Build Tools: $($buildToolsDirs[0].Name)" -ForegroundColor Gray

# Locate platform android.jar
$platformDirs = Get-ChildItem "$sdk\platforms" | Sort-Object Name -Descending
if ($platformDirs.Count -eq 0) {
    throw "No Android platform found in $sdk\platforms"
}
$androidJar = Join-Path $platformDirs[0].FullName "android.jar"
Write-Host "[+] Using Android Platform: $($platformDirs[0].Name)" -ForegroundColor Gray

# Tools
$aapt2 = Join-Path $buildTools "aapt2.exe"
$d8 = Join-Path $buildTools "d8.bat"
$zipalign = Join-Path $buildTools "zipalign.exe"
$apksigner = Join-Path $buildTools "apksigner.bat"

# Detect Java / JBR
$javaHome = $env:JAVA_HOME
if (-not $javaHome -or -not (Test-Path "$javaHome\bin\javac.exe")) {
    $asJbr = "C:\Program Files\Android\Android Studio\jbr"
    if (Test-Path "$asJbr\bin\javac.exe") {
        $javaHome = $asJbr
        $env:JAVA_HOME = $asJbr
    } else {
        throw "Could not locate JDK or Android Studio JBR."
    }
}
$javac = Join-Path $javaHome "bin\javac.exe"
$keytool = Join-Path $javaHome "bin\keytool.exe"
Write-Host "[+] Using Java: $javaHome" -ForegroundColor Gray

# 2. Sync Web Assets
Write-Host ""
Write-Host "[*] Syncing latest web assets..." -ForegroundColor Yellow
$assetWww = "android\app\src\main\assets\www"
$assetRoot = "android\app\src\main\assets"
New-Item -ItemType Directory -Force -Path $assetWww | Out-Null
Copy-Item -Path "index.html", "styles.css", "app.js" -Destination $assetWww -Force
Copy-Item -Path "index.html", "styles.css", "app.js" -Destination $assetRoot -Force
Write-Host "[OK] Web assets synchronized." -ForegroundColor Green

# 3. Clean & Prepare Build Directory
$buildDir = "android\build"
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
New-Item -ItemType Directory -Force -Path "$buildDir\gen", "$buildDir\classes", "$buildDir\dex" | Out-Null

# 4. Compile Resources (AAPT2)
Write-Host ""
Write-Host "[*] Compiling Android resources with AAPT2..." -ForegroundColor Yellow
& $aapt2 compile --dir "android\app\src\main\res" -o "$buildDir\compiled_res.zip"
if ($LASTEXITCODE -ne 0) { throw "AAPT2 compile failed" }

# 5. Link Resources & Generate R.java (Without -A to avoid Windows backslash bug)
Write-Host "[*] Linking resources with AAPT2..." -ForegroundColor Yellow
& $aapt2 link "$buildDir\compiled_res.zip" `
  -I $androidJar `
  --manifest "android\app\src\main\AndroidManifest.xml" `
  --java "$buildDir\gen" `
  -o "$buildDir\base_res.apk"
if ($LASTEXITCODE -ne 0) { throw "AAPT2 link failed" }

# 6. Compile Java Sources
Write-Host ""
Write-Host "[*] Compiling Java source code..." -ForegroundColor Yellow
$srcFiles = @(
  "$buildDir\gen\com\katsu\performance\R.java",
  "android\app\src\main\java\com\katsu\performance\KatsuBridge.java",
  "android\app\src\main\java\com\katsu\performance\MainActivity.java"
)
& $javac -cp $androidJar -d "$buildDir\classes" --release 8 $srcFiles
if ($LASTEXITCODE -ne 0) { throw "Java compilation failed" }

# 7. Convert Bytecode to Dalvik Executable (D8)
Write-Host "[*] Converting bytecode to classes.dex (D8)..." -ForegroundColor Yellow
$classFiles = (Get-ChildItem -Recurse "$buildDir\classes" -Filter "*.class").FullName
& $d8 --output "$buildDir\dex" --lib $androidJar $classFiles
if ($LASTEXITCODE -ne 0) { throw "D8 dexing failed" }

# 8. Package classes.dex and web assets with POSIX forward slashes
Write-Host ""
Write-Host "[*] Injecting classes.dex and assets with forward slashes into package..." -ForegroundColor Yellow
Copy-Item "$buildDir\base_res.apk" "$buildDir\unaligned.apk" -Force

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$unalignedPath = (Resolve-Path "$buildDir\unaligned.apk").Path
$zip = [System.IO.Compression.ZipFile]::Open($unalignedPath, [System.IO.Compression.ZipArchiveMode]::Update)

# 8a. Add classes.dex
$dexPath = (Resolve-Path "$buildDir\dex\classes.dex").Path
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $dexPath, "classes.dex")

# 8b. Add web assets with explicit forward slashes (both assets/www/ and assets/)
$htmlPath = (Resolve-Path "index.html").Path
$cssPath = (Resolve-Path "styles.css").Path
$jsPath = (Resolve-Path "app.js").Path

[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $htmlPath, "assets/www/index.html")
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $cssPath, "assets/www/styles.css")
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $jsPath, "assets/www/app.js")

[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $htmlPath, "assets/index.html")
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $cssPath, "assets/styles.css")
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $jsPath, "assets/app.js")

$zip.Dispose()
Write-Host "[OK] Forward-slash asset injection complete." -ForegroundColor Green

# 9. 4-byte Page Alignment (zipalign)
Write-Host "[*] Optimizing 4-byte page alignment (zipalign)..." -ForegroundColor Yellow
& $zipalign -f -p 4 "$buildDir\unaligned.apk" "$buildDir\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "Zipalign failed" }

# 10. Signing Key Setup & APK Signing
Write-Host ""
Write-Host "[*] Signing APK with v2/v3 signature scheme..." -ForegroundColor Yellow
if (-not (Test-Path $Keystore)) {
    Write-Host "[+] Generating release signing keystore ($Keystore)..." -ForegroundColor Cyan
    & $keytool -genkeypair -validity 10000 `
      -dname "CN=KATSU, OU=Mobile, O=KATSU AI, L=Cupertino, ST=CA, C=US" `
      -keystore $Keystore `
      -storepass $KeyPass `
      -keypass $KeyPass `
      -alias $KeyAlias `
      -keyalg "RSA" `
      -keysize 2048
}

& $apksigner sign `
  --ks $Keystore `
  --ks-pass "pass:$KeyPass" `
  --key-pass "pass:$KeyPass" `
  --ks-key-alias $KeyAlias `
  --out $OutputApk `
  "$buildDir\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "APK signing failed" }

# 11. Final Verification
Write-Host ""
Write-Host "[*] Verifying APK integrity and asset paths..." -ForegroundColor Yellow
& $apksigner verify --verbose $OutputApk

# Verify asset entries in the signed APK
$verifyZip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $OutputApk).Path)
Write-Host "[*] Verifying entries in final APK:" -ForegroundColor Cyan
$verifyZip.Entries | Where-Object { $_.FullName -match "assets|classes" } | ForEach-Object {
    Write-Host "    -> $($_.FullName)" -ForegroundColor Gray
}
$verifyZip.Dispose()

$apkItem = Get-Item $OutputApk
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host " [SUCCESS] APK BUILD COMPLETE!                  " -ForegroundColor Green
Write-Host " Output File: $($apkItem.FullName)" -ForegroundColor Cyan
Write-Host " Size:        $([Math]::Round($apkItem.Length / 1KB, 1)) KB" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Green
