# mirrulations-query: Docket Stats CLI

This command line tool prints, for a given regulations.gov docket ID:
- The number of unique JSON files for dockets, documents, and comments in the AWS Open Data S3 bucket (s3://mirrulations)
- The corresponding count from the regulations.gov API
- A side-by-side comparison for each type (docket, documents, comments)

The S3 bucket is part of the AWS Open Data initiative and can be accessed free of charge, without AWS credentials.

## Setup

1. The `setup.py` works with `pip` to create a command `mirrulations-fetch`.  It is recommended that you create a virtual environment and install locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

2. Create a `.env` file in the project root with your regulations.gov API key:

```
API_KEY=your_actual_api_key_here
```

You can use `DEMO_KEY` for testing, but it is rate-limited and for demo purposes only.  You can obtain an API key at the [Regulations.gov API documentation page](https://open.gsa.gov/api/regulationsgov/).

## Usage

Run the CLI tool with a docket ID:

```bash
docket-stats <DOCKET_ID>
```

### Example

```bash
$ docket-stats CMS-2025-0050
Gathering information (this may take a while for large dockets)...
Comments:  12%|██▍        | 120/981 [00:01<00:09, 91.23file/s]
Docket ID: CMS-2025-0050
Docket Title: Request for Information: Health Technology Ecosystem (CMS-0042-NC)
Docket JSON files (S3/API): 1/1
Documents JSON files (S3/API): 2/2
Comments JSON files (S3/API): 981/981
```

- The S3 count is the number of unique JSON files (ignoring duplicates with suffixes like (1), (2), etc.).
- The API count is from regulations.gov.
- The progress bar only appears for comments, and only for large dockets.

## Notes
- S3 queries may take a while for large dockets.
- No AWS credentials are required; the tool uses unsigned S3 access.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
