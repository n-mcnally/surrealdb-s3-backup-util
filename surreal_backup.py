import os
import json
import requests
import gzip
from datetime import datetime, timedelta
import boto3
import argparse

def load_config(config_path):
    """Load configuration from a JSON file."""
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def backup_surrealdb(config, ns, db):
    """Perform the backup process for SurrealDB."""
    # Ensure the backup directory exists
    os.makedirs(config['LOCAL_BACKUP_DIR'], exist_ok=True)

    # Define the backup file names
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    backup_file_name = f"{ns}-{db}-backup-{timestamp}.surql"
    backup_file_path = os.path.join(config['LOCAL_BACKUP_DIR'], backup_file_name)
    gzip_backup_file_path = f"{backup_file_path}.gz"

    # Perform the HTTP request to export data from SurrealDB
    response = requests.get(
        f"{config['SURRREAL_HOST']}/export",
        auth=(config['SURREAL_USER'], config['SURREAL_PASS']),
        headers={'NS': ns, 'DB': db, 'Accept': 'application/json'}
    )

    if response.status_code == 200:
        with open(backup_file_path, 'wb') as backup_file:
            backup_file.write(response.content)
        print(f"Backup successful: {backup_file_path}")
    else:
        print(f"Backup failed: {response.text}")
        exit(1)

    # Compress the backup file
    with open(backup_file_path, 'rb') as f_in, gzip.open(gzip_backup_file_path, 'wb') as f_out:
        f_out.writelines(f_in)
    print(f"Backup compressed: {gzip_backup_file_path}")

    # Delete the uncompressed backup file
    os.remove(backup_file_path)
    print(f"Uncompressed backup file deleted: {backup_file_path}")

    # Upload to S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=config['S3_ACCESS_KEY'],
        aws_secret_access_key=config['S3_SECRET_KEY'],
        region_name=config['S3_REGION']
    )
    s3_key = f"data/surrealdb/backups/{os.path.basename(gzip_backup_file_path)}"
    s3_client.upload_file(gzip_backup_file_path, config['S3_BUCKET'], s3_key)
    print(f"Backup uploaded to S3: {s3_key}")

def rotate_old_backups(config):
    """Delete old backups based on the retention period."""
    retention_period = datetime.utcnow() - timedelta(days=config['BACKUP_RETENTION_DAYS'])
    for root, _, files in os.walk(config['LOCAL_BACKUP_DIR']):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Extract the timestamp from the filename
                file_timestamp_str = file.split('-')[-2] + '-' + file.split('-')[-1].split('.')[0]
                file_timestamp = datetime.strptime(file_timestamp_str, "%Y-%m-%dT%H-%M-%S")
                if file_timestamp < retention_period:
                    os.remove(file_path)
                    print(f"Deleted old backup: {file_path}")
            except (ValueError, IndexError):
                # Skip files that don't match the expected format
                continue

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Backup SurrealDB data to S3.")
    default_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    parser.add_argument("--ns", type=str, help="Namespace to override the configuration value.")
    parser.add_argument("--db", type=str, help="Database to override the configuration value.")
    parser.add_argument("--config", type=str, default=default_config_path, help="Path to the configuration file.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config(args.config)

    ns = args.ns if args.ns else config['SURREAL_NS']
    db = args.db if args.db else config['SURREAL_DB']

    backup_surrealdb(config, ns, db)
    rotate_old_backups(config)

if __name__ == "__main__":
    main()
