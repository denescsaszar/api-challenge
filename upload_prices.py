import sys

import pandas as pd
import requests
from pydantic import BaseModel
from requests.auth import HTTPBasicAuth

API = "https://api-backend-olsgyubl4a-ew.a.run.app"
# API = "http://localhost:8000"


class Credentials(BaseModel):
    client_id: str
    client_secret: str

def get_access_token(credentials: Credentials) -> str:
    """
    Authenticate with the API using OAuth2 client credentials.
    Returns the access token for subsequent API calls.
    """
    response = requests.post(
        f"{API}/oauth2/v2.0/token",
        auth=HTTPBasicAuth(credentials.client_id, credentials.client_secret),
    )
    response.raise_for_status()
    return response.json()["access_token"]

# TODO: implement authentication and upload
def upload_prices(credentials: Credentials, data: pd.DataFrame):
    """
    Upload prices to the API in batches, handling backpressure.
    The API may accept fewer products than sent, so we retry remaining products.
    """
    # Get access token using our authentication function
    access_token = get_access_token(credentials)
    
    # Group prices by product_id (CSV has multiple rows per product)
    # This is like groupBy in JavaScript
    products_data = []
    for product_id, group in data.groupby('product_id'):
        prices = []
        for _, row in group.iterrows():
            prices.append({
                "market": row["market"],
                "channel": row["channel"],
                "price": float(row["price"]),
                "valid_from": row["valid_from"],
                "valid_until": row["valid_until"]
            })
        
        products_data.append({
            "product_id": int(product_id),
            "prices": prices
        })
    
# Upload in batches (max 1000 products per request)
    batch_size = 1000
    start_index = 0
    
    while start_index < len(products_data):
        batch = products_data[start_index:start_index + batch_size]
        
        response = requests.post(
            f"{API}/product-prices",
            json={"products": batch},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        
        num_imported = response.json()["num_imported"]
        start_index += num_imported
        
        print(f"Uploaded {num_imported} products (total: {start_index}/{len(products_data)})")
        
        # If API didn't accept all products (backpressure), retry
        if num_imported == 0:
            print("API backpressure - retrying...")
    
    print(f"\n✅ Successfully uploaded all {uploaded_count} products!")
    
    # Validate the upload
    response = requests.get(
        f"{API}/validate-product-prices",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    
    validation_result = response.json()
    
    print("\n=== Validation Results ===")
    print(f"Correct checksum: {validation_result['correct_checksum']}")
    print(f"GCS Upload URL: {validation_result['gcs_upload']['url']}")
    print(f"\n🎉 Challenge complete! Send the GCS URL to 7Learnings!")


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        creds = Credentials.model_validate_json(f.read())
    upload_prices(creds, pd.read_csv(sys.argv[2]))
