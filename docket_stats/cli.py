import os
import click
import requests
from dotenv import load_dotenv
import re
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from tqdm import tqdm

def get_api_key():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise click.ClickException("API_KEY not found in .env file.")
    return api_key

def get_docket(docket_id, api_key):
    url = f"https://api.regulations.gov/v4/dockets/{docket_id}"
    params = {"api_key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def get_documents_count(docket_id, api_key):
    url = f"https://api.regulations.gov/v4/documents"
    params = {"filter[docketId]": docket_id, "api_key": api_key, "page[size]": 5}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("meta", {}).get("totalElements", 0)

def get_comments_count(docket_id, api_key):
    url = f"https://api.regulations.gov/v4/comments"
    params = {"filter[docketId]": docket_id, "api_key": api_key, "page[size]": 5}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("meta", {}).get("totalElements", 0)

def get_org_from_docket_id(docket_id):
    return docket_id.split('-')[0]

def list_unique_json_files(s3_client, bucket, prefix, show_progress=False, total_expected=None):
    paginator = s3_client.get_paginator('list_objects_v2')
    unique_names = set()
    if show_progress and total_expected:
        pbar = tqdm(total=total_expected, desc="Comments", unit="file")
    else:
        pbar = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.json'):
                base = re.sub(r'(?:\([0-9]+\))+\.json$', '.json', key.rsplit('/', 1)[-1])
                if base not in unique_names:
                    unique_names.add(base)
                    if pbar:
                        pbar.update(1)
    if pbar:
        pbar.close()
    return len(unique_names)

@click.command()
@click.argument("docket_id")
def main(docket_id):
    api_key = get_api_key()
    try:
        click.echo("Gathering information (this may take a while for large dockets)...")
        docket = get_docket(docket_id, api_key)
        documents_count = get_documents_count(docket_id, api_key)
        comments_count = get_comments_count(docket_id, api_key)
        org = get_org_from_docket_id(docket_id)
        s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        bucket = 'mirrulations'
        s3_base = f"raw-data/{org}/{docket_id}/text-{docket_id}"
        s3_stats = {}
        for sub in ['docket', 'documents', 'comments']:
            prefix = f"{s3_base}/{sub}/"
            if sub == 'comments':
                s3_count = list_unique_json_files(s3_client, bucket, prefix, show_progress=True, total_expected=comments_count)
            else:
                s3_count = list_unique_json_files(s3_client, bucket, prefix)
            api_count = 1 if sub == 'docket' else documents_count if sub == 'documents' else comments_count
            s3_stats[sub] = (s3_count, api_count)
        click.echo(f"Docket ID: {docket_id}")
        click.echo(f"Docket Title: {docket['data']['attributes'].get('title', 'N/A')}")
        for sub in ['docket', 'documents', 'comments']:
            s3_count, api_count = s3_stats[sub]
            click.echo(f"{sub.capitalize()} JSON files (S3/API): {s3_count}/{api_count}")
    except requests.HTTPError as e:
        click.echo(f"HTTP error: {e}", err=True)
        if e.response is not None:
            click.echo(e.response.text, err=True)
        exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        exit(1)

if __name__ == "__main__":
    main() 