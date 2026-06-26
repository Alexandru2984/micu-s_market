#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${MAILCOW_POSTFIX_CONTAINER:-mailcowdockerized-postfix-mailcow-1}"
CHAIN="${MAILCOW_CHAIN:-MAILCOW}"
QUEUE_MAX_MESSAGES="${MAILCOW_QUEUE_MAX_MESSAGES:-20}"
DEFERRED_MAX_MESSAGES="${MAILCOW_DEFERRED_MAX_MESSAGES:-5}"
RUN_SMTP_PROBE="${MAILCOW_RUN_SMTP_PROBE:-1}"
SMTP_PROBE_HOST="${MAILCOW_SMTP_PROBE_HOST:-98.136.96.76}"
SMTP_PROBE_PORT="${MAILCOW_SMTP_PROBE_PORT:-25}"
SMTP_PROBE_TIMEOUT="${MAILCOW_SMTP_PROBE_TIMEOUT:-20}"

fail() {
  echo "FAIL mailcow-delivery: $*" >&2
  exit 1
}

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  fail "this script must run as root to inspect iptables and Docker"
fi

docker inspect "$CONTAINER" >/dev/null 2>&1 || fail "container $CONTAINER not found"

iptables -C "$CHAIN" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null \
  || fail "missing RELATED,ESTABLISHED accept rule in iptables chain $CHAIN"

queue_json="$(docker exec "$CONTAINER" postqueue -j 2>/dev/null || true)"
if [[ -n "$queue_json" ]]; then
  queue_messages="$(printf '%s\n' "$queue_json" | sed '/^[[:space:]]*$/d' | wc -l)"
  deferred_messages="$(printf '%s\n' "$queue_json" | grep -Ec '"queue_name"[[:space:]]*:[[:space:]]*"deferred"' || true)"
else
  queue_messages=0
  deferred_messages=0
fi

if (( queue_messages > QUEUE_MAX_MESSAGES )); then
  fail "postfix queue has $queue_messages messages, threshold is $QUEUE_MAX_MESSAGES"
fi

if (( deferred_messages > DEFERRED_MAX_MESSAGES )); then
  fail "postfix deferred queue has $deferred_messages messages, threshold is $DEFERRED_MAX_MESSAGES"
fi

if [[ "$RUN_SMTP_PROBE" == "1" ]]; then
  banner="$(
    timeout "$SMTP_PROBE_TIMEOUT" docker exec \
      -e SMTP_PROBE_HOST="$SMTP_PROBE_HOST" \
      -e SMTP_PROBE_PORT="$SMTP_PROBE_PORT" \
      "$CONTAINER" sh -lc \
        'curl -sS --connect-timeout 8 --max-time 18 "telnet://${SMTP_PROBE_HOST}:${SMTP_PROBE_PORT}" | head -n 1' \
      2>&1 || true
  )"
  if [[ ! "$banner" =~ ^220[[:space:]] ]]; then
    fail "SMTP probe to $SMTP_PROBE_HOST:$SMTP_PROBE_PORT did not return a 220 banner: $banner"
  fi
fi

echo "OK mailcow-delivery: queue=$queue_messages deferred=$deferred_messages smtp_probe=$RUN_SMTP_PROBE"
