#!/usr/bin/env bash
# ==============================================================================
# Credit-Protection Watchdog & Automated Teardown Daemon
# Monitors GPU activity and idle time on DigitalOcean MI300X droplets.
# Automatically destroys or shuts down the droplet to prevent credit burn.
# ==============================================================================
set -euo pipefail

IDLE_LIMIT_MINUTES="${IDLE_LIMIT_MINUTES:-20}"
MAX_UPTIME_HOURS="${MAX_UPTIME_HOURS:-36}"
CHECK_INTERVAL_SECONDS=60

DO_API_TOKEN="${DIGITALOCEAN_TOKEN:-}"
DROPLET_ID="${DO_DROPLET_ID:-}"

echo "=========================================================="
echo " Starting Credit-Protection Watchdog Daemon"
echo " Idle Limit: ${IDLE_LIMIT_MINUTES}m | Max Uptime: ${MAX_UPTIME_HOURS}h"
echo "=========================================================="

START_TIMESTAMP=$(date +%s)
IDLE_MINUTES=0

destroy_droplet() {
    REASON="$1"
    echo ""
    echo "=========================================================="
    echo " [!] TRIGGERING AUTOMATED TEARDOWN: ${REASON}"
    echo "=========================================================="
    
    # 1. Try DigitalOcean API Deletion (Stops billing completely)
    if [ -n "$DO_API_TOKEN" ] && [ -n "$DROPLET_ID" ]; then
        echo "[*] Deleting droplet via DigitalOcean API (ID: ${DROPLET_ID})..."
        curl -s -X DELETE \
            -H "Authorization: Bearer ${DO_API_TOKEN}" \
            -H "Content-Type: application/json" \
            "https://api.digitalocean.com/v2/droplets/${DROPLET_ID}" || true
        echo "[+] Droplet deletion request sent."
    fi

    # 2. Hard fallback shutdown (powers down VM)
    echo "[*] Executing system emergency shutdown..."
    sudo shutdown -h now || poweroff
    exit 0
}

# Main Watchdog Loop
while true; do
    sleep "$CHECK_INTERVAL_SECONDS"

    CURRENT_TIMESTAMP=$(date +%s)
    UPTIME_SECONDS=$((CURRENT_TIMESTAMP - START_TIMESTAMP))
    MAX_UPTIME_SECONDS=$((MAX_UPTIME_HOURS * 3600))

    # Check 1: Max Uptime Ceiling Exceeded
    if [ "$UPTIME_SECONDS" -ge "$MAX_UPTIME_SECONDS" ]; then
        destroy_droplet "Maximum allowed instance uptime (${MAX_UPTIME_HOURS}h) reached."
    fi

    # Check 2: Check if batch runner process is actively running
    if pgrep -f "remote_batch_runner.py" > /dev/null; then
        IDLE_MINUTES=0
        continue
    fi

    # Check 3: Inspect GPU compute utilization via rocm-smi
    GPU_USE=0
    if command -v rocm-smi &> /dev/null; then
        # Extract GPU use percentage (0-100)
        GPU_USE=$(rocm-smi --showuse | grep -Eo '[0-9]+%' | head -1 | tr -d '%' || echo "0")
    fi

    if [ "$GPU_USE" -lt 5 ]; then
        IDLE_MINUTES=$((IDLE_MINUTES + 1))
        echo "[Watchdog] Droplet idle (GPU: ${GPU_USE}%, Runner inactive). Idle count: ${IDLE_MINUTES}/${IDLE_LIMIT_MINUTES}m"
        if [ "$IDLE_MINUTES" -ge "$IDLE_LIMIT_MINUTES" ]; then
            destroy_droplet "Droplet idle for more than ${IDLE_LIMIT_MINUTES} minutes without active runner."
        fi
    else
        IDLE_MINUTES=0
    fi
done
