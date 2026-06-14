#!/usr/bin/env bash

check_env_file_permissions() {
  local env_file="${1:-.env}"

  if [[ ! -f "$env_file" ]]; then
    return 0
  fi

  local mode
  mode="$(stat -c '%a' "$env_file")"
  if (( (8#$mode & 077) != 0 )); then
    echo "$env_file permissions are too open ($mode). Run: chmod 600 $env_file" >&2
    return 1
  fi
}

check_sensitive_file_permissions() {
  local failed=0
  local file
  shopt -s nullglob
  local files=(
    backup_seed.json
    *.sql
    *.dump
    *.backup
  )
  shopt -u nullglob

  for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
      continue
    fi

    local mode
    mode="$(stat -c '%a' "$file")"
    if (( (8#$mode & 077) != 0 )); then
      echo "$file permissions are too open ($mode). Run: chmod 600 $file" >&2
      failed=1
    fi
  done

  return "$failed"
}
