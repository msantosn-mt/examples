import os
import json
from woocommerce import API

# Create an instance of the WooCommerce API client
wcapi = API(
    url="",
    consumer_key="",
    consumer_secret="",
    version=""
)

def getProductData():
    # Retrieve all products with an empty SKU
    page = 1
    per_page = 100

    while True:
        # Send API request to retrieve products for the current page
        products = wcapi.get("products", params={"page": page, "per_page": per_page})

        if products.status_code != 200:
            print(f"Error: {products.status_code} - {products.json()}")
            break

        products_data = products.json()

        # Save each product as a separate JSON file
        for product in products_data:
            product_id = product['id']
            file_path = os.path.join(data_directory, f"product_{product_id}.json")

            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(product, file, ensure_ascii=False)

        # Check if there are more pages to fetch
        if len(products_data) < per_page:
            break
        print ("Page: " + str(page))
        page += 1
        

# Create a subdirectory for storing product data
data_directory = "products"
os.makedirs(data_directory, exist_ok=True)
getProductData()
