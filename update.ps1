# ============================================================
#  PUBLISH THE VAULT
#  Puts a newly-saved TheVault.html online at the live URL.
#
#  Usage:
#    .\update.ps1                     <- uses the newest TheVault*.html in Downloads
#    .\update.ps1 "C:\path\to\file"   <- uses the file you name
# ============================================================

param([string]$File)

$ErrorActionPreference = "Stop"
$SiteUrl = "https://dosenft.github.io/dwk-vault/"

# Step 0: work inside the folder this script lives in, no matter where it was run from.
Set-Location $PSScriptRoot

# Step 1: figure out which file to publish.
# If you didn't name one, grab the most recently saved TheVault*.html from Downloads.
if (-not $File) {
    $newest = Get-ChildItem "$env:USERPROFILE\Downloads" -Filter "TheVault*.html" |
              Sort-Object LastWriteTime -Descending |
              Select-Object -First 1
    if (-not $newest) {
        Write-Host "No TheVault*.html found in Downloads. Save it there, or pass the path." -ForegroundColor Red
        exit 1
    }
    $File = $newest.FullName
}

if (-not (Test-Path $File)) {
    Write-Host "That file doesn't exist: $File" -ForegroundColor Red
    exit 1
}

Write-Host "Publishing: $File"
Write-Host "   saved at: $((Get-Item $File).LastWriteTime)"

# Step 2: copy the file in, exactly as-is, and add the one line that
# asks Google not to list the site. We work in raw bytes so the copy is
# byte-for-byte perfect and the special characters never get mangled.
$bytes  = [System.IO.File]::ReadAllBytes($File)
$anchor = [System.Text.Encoding]::ASCII.GetBytes('<meta charset="utf-8">')
$robots = [System.Text.Encoding]::ASCII.GetBytes("`n" + '<meta name="robots" content="noindex, nofollow">')

# Is the robots line already in there? If so we don't add a second one.
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
if ($text -match 'name="robots"') {
    [System.IO.File]::WriteAllBytes("index.html", $bytes)
    Write-Host "   robots line already present - copied as-is."
}
else {
    # Find where <meta charset="utf-8"> ends, and slot the robots line in right after it.
    $idx = -1
    for ($i = 0; $i -le $bytes.Length - $anchor.Length; $i++) {
        $ok = $true
        for ($j = 0; $j -lt $anchor.Length; $j++) {
            if ($bytes[$i + $j] -ne $anchor[$j]) { $ok = $false; break }
        }
        if ($ok) { $idx = $i; break }
    }
    if ($idx -lt 0) {
        Write-Host "Couldn't find <meta charset=`"utf-8`"> in that file - is it really the vault?" -ForegroundColor Red
        exit 1
    }
    $at  = $idx + $anchor.Length
    $out = New-Object byte[] ($bytes.Length + $robots.Length)
    [Array]::Copy($bytes, 0, $out, 0, $at)
    [Array]::Copy($robots, 0, $out, $at, $robots.Length)
    [Array]::Copy($bytes, $at, $out, $at + $robots.Length, $bytes.Length - $at)
    [System.IO.File]::WriteAllBytes("index.html", $out)
    Write-Host "   robots line added."
}

# Step 3: safety check - never let a recording get committed by accident.
# They are huge and belong in the release, not in the repo.
$big = Get-ChildItem -File | Where-Object { $_.Length -gt 25MB }
if ($big) {
    Write-Host "Stopping: these files are too big to commit:" -ForegroundColor Red
    $big | ForEach-Object { Write-Host "   $($_.Name)" }
    exit 1
}

# Step 4: save the change and send it to GitHub.
git add index.html

# If nothing actually changed, stop here instead of making an empty commit.
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes - the site already matches this file. Nothing to publish." -ForegroundColor Yellow
    exit 0
}
git commit -m "Update vault"
git push

# Step 5: tell you where it is.
Write-Host ""
Write-Host "Published: $SiteUrl" -ForegroundColor Green
Write-Host "GitHub takes about a minute to update."
Write-Host "If you still see the old version, press Ctrl+Shift+R to force a fresh load." -ForegroundColor Cyan
