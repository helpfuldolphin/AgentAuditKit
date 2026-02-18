#!/usr/bin/env pwsh
# Agent Audit Kit - Deterministic Demo Runner
# For screen capture and live demonstration
#
# Usage: ./demo/run_demo.ps1

$ErrorActionPreference = "Stop"
$DemoOutput = "./demo_output"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " AGENT AUDIT KIT - Evidence Capture Demo" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " This demo shows:" -ForegroundColor Yellow
Write-Host "   1. Real-time capture of agent tool calls"
Write-Host "   2. Hash-chained evidence storage"
Write-Host "   3. Threat detection with OWASP ASI mapping"
Write-Host "   4. Portable bundle export with standalone verification"
Write-Host ""
Write-Host " Press Enter to begin..." -ForegroundColor Green
Read-Host

# Step 1: Clear previous output
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " STEP 1: Clearing previous demo output" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
if (Test-Path $DemoOutput) {
    Remove-Item -Recurse -Force $DemoOutput
    Write-Host " [OK] Removed $DemoOutput" -ForegroundColor Green
} else {
    Write-Host " [OK] No previous output to clear" -ForegroundColor Green
}
Start-Sleep -Seconds 1

# Step 2: Run the real capture demo
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " STEP 2: Running agent capture (mock OpenAI client)" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
python examples/real_capture_demo.py --output $DemoOutput --mock
Write-Host ""
Start-Sleep -Seconds 2

# Step 3: Verify the bundle
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " STEP 3: Verifying evidence bundle integrity" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Push-Location "$DemoOutput/bundle"
python verify.py
Pop-Location
Start-Sleep -Seconds 2

# Step 4: Show threat flags summary
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " STEP 4: Threat Detection Summary" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

$manifest = Get-Content "$DemoOutput/bundle/replay_manifest.json" | ConvertFrom-Json
$bundleId = if ($manifest.bundle_id) { $manifest.bundle_id } else { $manifest.run_id }
Write-Host " Bundle ID:     $bundleId" -ForegroundColor Cyan
Write-Host " Event Count:   $($manifest.event_count)" -ForegroundColor Cyan
Write-Host " Chain Head:    $($manifest.chain_head.Substring(0,16))..." -ForegroundColor Cyan
Write-Host ""

if ($manifest.threat_flags -and $manifest.threat_flags.Count -gt 0) {
    Write-Host " THREAT FLAGS DETECTED:" -ForegroundColor Yellow
    Write-Host ""
    foreach ($flag in $manifest.threat_flags) {
        $severity = $flag.severity.ToUpper()
        $color = switch ($severity) {
            "CRITICAL" { "Red" }
            "HIGH" { "Red" }
            "MEDIUM" { "Yellow" }
            "LOW" { "DarkYellow" }
            default { "White" }
        }
        Write-Host "   [$severity] $($flag.threat_class)" -ForegroundColor $color
        Write-Host "   OWASP Tags: $($flag.owasp_asi_tags -join ', ')" -ForegroundColor Gray
        Write-Host "   $($flag.description)" -ForegroundColor Gray
        Write-Host ""
    }
} else {
    Write-Host " No threat flags detected." -ForegroundColor Green
}

# Final summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DEMO COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Evidence artifacts created:" -ForegroundColor White
Write-Host "   - Vault:    $DemoOutput/vault/" -ForegroundColor Gray
Write-Host "   - Bundle:   $DemoOutput/bundle/" -ForegroundColor Gray
Write-Host "   - Manifest: $DemoOutput/bundle/replay_manifest.json" -ForegroundColor Gray
Write-Host "   - Verify:   $DemoOutput/bundle/verify.py" -ForegroundColor Gray
Write-Host ""
Write-Host " This bundle can be:" -ForegroundColor Yellow
Write-Host "   - Attached to incident reports"
Write-Host "   - Supplied to insurers or regulators"
Write-Host "   - Verified independently (no AAK installation required)"
Write-Host ""
Write-Host " Agent Audit Kit produces evidence artifacts, not truth claims." -ForegroundColor DarkGray
Write-Host ""
