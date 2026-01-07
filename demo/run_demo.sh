#!/usr/bin/env bash
# Agent Audit Kit - Deterministic Demo Runner
# For screen capture and live demonstration
#
# Usage: ./demo/run_demo.sh

set -e
DEMO_OUTPUT="./demo_output"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} AGENT AUDIT KIT - Evidence Capture Demo${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${YELLOW} This demo shows:${NC}"
echo "   1. Real-time capture of agent tool calls"
echo "   2. Hash-chained evidence storage"
echo "   3. Threat detection with OWASP ASI mapping"
echo "   4. Portable bundle export with standalone verification"
echo ""
echo -e "${GREEN} Press Enter to begin...${NC}"
read -r

# Step 1: Clear previous output
echo ""
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo -e "${WHITE} STEP 1: Clearing previous demo output${NC}"
echo -e "${GRAY}------------------------------------------------------------${NC}"
if [ -d "$DEMO_OUTPUT" ]; then
    rm -rf "$DEMO_OUTPUT"
    echo -e "${GREEN} [OK] Removed $DEMO_OUTPUT${NC}"
else
    echo -e "${GREEN} [OK] No previous output to clear${NC}"
fi
sleep 1

# Step 2: Run the real capture demo
echo ""
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo -e "${WHITE} STEP 2: Running agent capture (mock OpenAI client)${NC}"
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo ""
python examples/real_capture_demo.py --output "$DEMO_OUTPUT" --mock
echo ""
sleep 2

# Step 3: Verify the bundle
echo ""
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo -e "${WHITE} STEP 3: Verifying evidence bundle integrity${NC}"
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo ""
cd "$DEMO_OUTPUT/bundle"
python verify.py
cd - > /dev/null
sleep 2

# Step 4: Show threat flags summary
echo ""
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo -e "${WHITE} STEP 4: Threat Detection Summary${NC}"
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo ""

# Parse manifest with Python
python3 << PYEOF
import json
with open("$DEMO_OUTPUT/bundle/replay_manifest.json") as f:
    m = json.load(f)

print(f" Bundle ID:     \033[0;36m{m['run_id']}\033[0m")
print(f" Event Count:   \033[0;36m{m['event_count']}\033[0m")
print(f" Chain Head:    \033[0;36m{m['chain_head'][:16]}...\033[0m")
print()

flags = m.get("threat_flags", [])
if flags:
    print(" \033[1;33mTHREAT FLAGS DETECTED:\033[0m")
    print()
    for flag in flags:
        sev = flag["severity"].upper()
        color = {"CRITICAL": "31", "HIGH": "31", "MEDIUM": "33", "LOW": "33"}.get(sev, "0")
        print(f"   \033[{color}m[{sev}] {flag['threat_class']}\033[0m")
        print(f"   \033[90mOWASP Tags: {', '.join(flag['owasp_asi_tags'])}\033[0m")
        print(f"   \033[90m{flag['description']}\033[0m")
        print()
else:
    print(" \033[0;32mNo threat flags detected.\033[0m")
PYEOF

# Final summary
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} DEMO COMPLETE${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${WHITE} Evidence artifacts created:${NC}"
echo -e "${GRAY}   - Vault:    $DEMO_OUTPUT/vault/${NC}"
echo -e "${GRAY}   - Bundle:   $DEMO_OUTPUT/bundle/${NC}"
echo -e "${GRAY}   - Manifest: $DEMO_OUTPUT/bundle/replay_manifest.json${NC}"
echo -e "${GRAY}   - Verify:   $DEMO_OUTPUT/bundle/verify.py${NC}"
echo ""
echo -e "${YELLOW} This bundle can be:${NC}"
echo "   - Attached to incident reports"
echo "   - Supplied to insurers or regulators"
echo "   - Verified independently (no AAK installation required)"
echo ""
echo -e "${GRAY} Agent Audit Kit produces evidence artifacts, not truth claims.${NC}"
echo ""
