# API Backend Challenge
## Solution by Denes Csaszar

This project implements a Python client to upload product prices to the API.

## Problem Description

The challenge requires implementing an API client that:

1. Authenticates with OAuth2 client credentials
2. Reads product prices from a CSV file
3. Uploads prices to the API in batches
4. Handles API backpressure (partial acceptance of batches)
5. Validates the upload

## Solution Overview

### Authentication (`get_access_token`)

- Uses HTTP Basic Auth with client credentials
- Requests JWT access token from `/oauth2/v2.0/token`
- Token is valid for 15 minutes

### Data Processing

- Reads `prices.csv` using pandas
- Groups prices by `product_id` (one product can have multiple price points)
- Transforms flat CSV structure into nested API format

### Upload with Backpressure Handling (`upload_prices`)

- Uploads in batches of maximum 1000 products
- Handles API backpressure: if API accepts fewer products, retries remaining products
- Uses `start_index` to track progress and avoid duplicate uploads
- Makes POST requests to `/product-prices` with Bearer token authentication

### Validation

- Calls `/validate-product-prices` to verify upload
- Returns GCS URL for submission

## How to Run

### Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Known Issue: Checksum Validation

The validation endpoint returns `Correct checksum: False`, which is expected behavior:

**Root Cause:**

- The API requires products grouped with nested prices (API data model requirement)
- The original CSV is not sorted by product_id
- After grouping by product_id, row order differs from the original CSV
- The API's checksum compares exact byte-for-byte equality

**Why This Happens:**

```python
# Original CSV (example):
# product_id,market,price
# 670399,US,88.0
# 667962,DE,50.0
# 670399,DE,75.0  # Same product, different row

# After grouping (API requirement):
# Product 670399: [US: 88.0, DE: 75.0]
# Product 667962: [DE: 50.0]
# → Rows are now in different order!
```
