#!/usr/bin/env python3
"""Încarcă un fișier de backup în Cloudflare R2 (S3-compatibil) și curăță
backup-urile offsite mai vechi decât retenția. Configurare din environment:

  R2_ENDPOINT_URL, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
  R2_BACKUP_PREFIX (opțional, implicit "postgres/")
  BACKUP_RETENTION_DAYS (opțional, implicit 14)
"""
import datetime
import os
import sys

import boto3
from botocore.config import Config


def main():
    if len(sys.argv) < 2:
        print("usage: r2_upload.py <file>", file=sys.stderr)
        return 2
    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"file not found: {path}", file=sys.stderr)
        return 2

    try:
        endpoint = os.environ["R2_ENDPOINT_URL"]
        bucket = os.environ["R2_BUCKET"]
        access_key = os.environ["R2_ACCESS_KEY_ID"]
        secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    except KeyError as exc:
        print(f"missing env var: {exc}", file=sys.stderr)
        return 2

    prefix = os.environ.get("R2_BACKUP_PREFIX", "postgres/")
    retention = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    key = prefix + os.path.basename(path)
    s3.upload_file(path, bucket, key)
    print(f"uploaded s3://{bucket}/{key}")

    # Retenție offsite: șterge obiectele mai vechi decât retention zile.
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention)
    deleted = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                s3.delete_object(Bucket=bucket, Key=obj["Key"])
                deleted += 1
    if deleted:
        print(f"pruned {deleted} old offsite backup(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
