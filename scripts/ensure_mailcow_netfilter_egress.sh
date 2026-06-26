#!/usr/bin/env bash
set -euo pipefail

CHAIN="${MAILCOW_CHAIN:-MAILCOW}"

rule=(-m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT)

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "this script must run as root to inspect and update iptables" >&2
  exit 1
fi

if ! iptables -S "$CHAIN" >/dev/null 2>&1; then
  echo "iptables chain $CHAIN not found; is mailcow netfilter initialized?" >&2
  exit 1
fi

if ! iptables -C "$CHAIN" "${rule[@]}" 2>/dev/null; then
  iptables -I "$CHAIN" 1 "${rule[@]}"
fi

iptables -C "$CHAIN" "${rule[@]}"
