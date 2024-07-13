# SurrealDB Backup to S3 Script

Very simple utility to export data from a SurrealDB database, compresses it, and upload a copy to an AWS S3 bucket. It also handles local backup rotation and relies on AWS S3 lifecycle policies for S3-side rotation.

Installation provides the `surreal_backup` cli utility, crontab rules can be setup to schedule backups.
    
## Prerequisites

- Python 3.x
- AWS S3 bucket
- AWS credentials configured with appropriate permissions
- AWS dashboard or CLI access for bucket policy setup.
    
## Installation Notes

### Install Python and Pip

- Ensure Python 3 and `pip` are installed on your system:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip
  ```

### Install Required Python Packages

- Install the required Python packages using `pip`:
  ```bash
  pip3 install boto3 requests
  ```

### Setup with setuptools

- Install the script as a CLI tool:
  ```bash
  sudo python3 setup.py install
  ```

### Configuration File

- Create a JSON configuration file (`config.json`) in the same directory (or using `--config` arg) with the following content:
  ```json
  {
    "S3_ACCESS_KEY": "your_s3_access_key",
    "S3_SECRET_KEY": "your_s3_secret_key",
    "S3_BUCKET": "your_s3_bucket_name",
    "S3_REGION": "your_s3_region",
    "SURREAL_USER": "your_surrealdb_user",
    "SURREAL_PASS": "your_surrealdb_password",
    "LOCAL_BACKUP_DIR": "/var/lib/surrealdb/backups",
    "SURREAL_NS": "your_namespace",
    "SURREAL_DB": "your_database",
    "SURRREAL_HOST": "http://localhost:8000",
    "BACKUP_RETENTION_DAYS": 7
  }
  ```
- Replace the placeholder values with your actual values.

### Set Directory and File Permissions

- Change ownership of the directory and files to your user:
  ```bash
  sudo chown -R <youruser>:<youruser> /var/lib/surrealdb/backups
  ```
  Replace `<youruser>` with your actual username.

- Set appropriate permissions:
  ```bash
  sudo chmod -R 750 /var/lib/surrealdb/backups
  sudo chmod 640 /var/lib/surrealdb/backups/config.json
  ```

- Verify the effective permissions:
  ```bash
  namei -l /var/lib/surrealdb/backups/config.json
  ```

## Usage Notes

- **Run the Script Manually**:
  - Ensure the script is executable:
    ```bash
    sudo chmod +x /var/lib/surrealdb/backups/surreal_backup.py
    ```
  - Run the script with default values from the configuration file using `sudo`:
    ```bash
    sudo surreal-backup
    ```
  - Override the namespace and database from the command line using `sudo`:
    ```bash
    sudo surreal-backup --ns new_namespace --db new_database
    ```

- **Schedule the Script with Cron**:
  - Add a cron job to run the backup script automatically (e.g., daily at 2 AM):
    ```bash
    sudo crontab -e
    ```
  - Add the following line to the crontab to overwrite the log file with each run:
    ```bash
    0 2 * * * /usr/bin/surreal-backup > /var/lib/surrealdb/backups/backup.log 2>&1
    ```

## AWS S3 Setup

- **Create an S3 Bucket**:
  - Go to the S3 console, create a bucket, and follow the prompts.
  
- **Set Up a Lifecycle Policy**:
  - Navigate to your S3 bucket, go to the "Management" tab, and create a lifecycle rule.
  - Add an expiration action to delete objects older than the specified number of days (e.g., 7 days).

### Example Lifecycle Policy JSON

- Use the AWS CLI to apply a lifecycle policy with the following JSON:
  ```json
  {
    "Rules": [
      {
        "ID": "Delete old backups",
        "Prefix": "backups/",
        "Status": "Enabled",
        "Expiration": {
          "Days": 7
        }
      }
    ]
  }
  ```
- Apply the policy:
  ```bash
  aws s3api put-bucket-lifecycle-configuration --bucket your_bucket_name --lifecycle-configuration file://lifecycle.json
  ```

## Script Actions

- **Load Configuration**: Reads the configuration from `config.json`.
- **Ensure Backup Directory**: Ensures the local backup directory exists.
- **Export Data**: Exports data from SurrealDB using the HTTP endpoint and saves it locally.
- **Compress the Backup**: Compresses the backup file using gzip.
- **Upload to S3**: Uploads the compressed file to the specified S3 bucket and prefix.
- **Rotate Local Backups**: Deletes local backups older than the specified retention period.
- **S3 Lifecycle Policy**: Manages the deletion of old backups in S3 based on the lifecycle policy.
- **Command-line Overrides**: Supports overriding the namespace (`NS`) and database (`DB`) using command-line arguments.