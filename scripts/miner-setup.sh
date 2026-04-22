#!/usr/bin/env bash
# Install and configure local miners for solo Bitcoin mining.
# Usage:  bash scripts/miner-setup.sh [--cpu] [--nvidia] [--amd] [OPTIONS]
#
# Hardware flags (opt-in):
#   --cpu             install and configure cpuminer-opt
#   --nvidia          install and configure ccminer (requires CUDA)
#   --amd             install and configure cgminer (requires OpenCL)
#
# Configuration options (passed through to `miner configure`):
#   --address ADDR    Bitcoin address  (default: read from KeePassXC)
#   --worker NAME     worker label     (default: desk)
#   --proxy-host H    Stratum host     (default: 127.0.0.1)
#   --proxy-port P    Stratum port     (default: 3333)
#   --threads N       CPU thread count (default: auto, cpuminer only)
#   --auto-pass-env F path to auto-pass env file for address lookup
#
# After this script completes:
#   systemctl --user daemon-reload
#   systemctl --user start bit-byte-block-cpu-miner.service    # if --cpu
#   systemctl --user start bit-byte-block-nvidia-miner.service # if --nvidia
#   systemctl --user start bit-byte-block-amd-miner.service    # if --amd
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Separate hardware flags from configure-only flags so install gets a clean list.
HARDWARE_FLAGS=()
CONFIGURE_FLAGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cpu|--nvidia|--amd)
            HARDWARE_FLAGS+=("$1")
            CONFIGURE_FLAGS+=("$1")
            shift ;;
        *)
            CONFIGURE_FLAGS+=("$1")
            shift ;;
    esac
done

if [[ ${#HARDWARE_FLAGS[@]} -eq 0 ]]; then
    echo "error: specify at least one of --cpu, --nvidia, --amd" >&2
    exit 1
fi

echo "==> Installing miner binaries ..."
python3 -m bit_byte_block miner install "${HARDWARE_FLAGS[@]}"

echo ""
echo "==> Writing miner configs and installing systemd units ..."
python3 -m bit_byte_block miner configure "${CONFIGURE_FLAGS[@]}"
