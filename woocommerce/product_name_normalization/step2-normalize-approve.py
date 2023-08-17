import os
import json
import re
import html
from woocommerce import API

# Create an instance of the WooCommerce API client
wcapi = API(
    url="https://www.mrwhiskers.shop",
    consumer_key="ck_3b9d62f01fa0dfcbf76902b20942b86b22492855",
    consumer_secret="cs_73a03c9fed4f2dbef4bd5346406aff2673d06566",
    version="wc/v3",
    timeout=10
)

# Define the list of brand names
brand_names = [
    "Biokats",
    "Beaphar",
    "Benelux",
    "Butcher's",
    "Bob Martin",
    "Ebi",
    "Classic",
    "Durapet",
    "Gimbi",
    "Stimulfos",
    "Cat&Co",
    "D&D",
    "Royal Canin",
    "Drinkwell",
    "Puur Pauze",
    "Brit",
    "Duvo",
    "Lindocat",
    "Schesir",
    "Gemon",
    "Moderna",
    "Monge",
    "Stuzzy",
    "Woodycat",
    "PetSafe",
    "Scruffs",
    "Trixie",
    "Vetzyme"
]

def createAtomicUpdateDataFile(file_path, atomic_data):
   with open(file_path, 'w', encoding='utf-8') as file:

def updateProductDataFile(file_path):
   with open(file_path, 'w', encoding='utf-8') as file:
      json.dump(updated_product, file, ensure_ascii=False)

def move_match_to_end(string, regex_pattern):
    match = re.search(regex_pattern, string, flags=re.IGNORECASE)
    matched_string = match.group(0)
    modified_string = re.sub(regex_pattern, "", string, flags=re.IGNORECASE) + " - " + matched_string.upper()
    return modified_string.strip()

    # Create a subdirectory for storing product data
data_directory = "products"
os.makedirs(data_directory, exist_ok=True)

#getProductData()

# Iterate over the saved product files and retrieve their details
for file_name in os.listdir(data_directory):
    file_path = os.path.join(data_directory, file_name)

    with open(file_path, 'r', encoding='utf-8') as file:
        product = json.load(file)
        product_name = product['name'].encode('utf-8')

        if product_name.isupper():
            new_product_name = product_name.title()
            new_product_name = new_product_name.decode('utf-8')
            updated_product = {
                "name": new_product_name  # Apply title capitalization rule
            }

            # Identify the brand in the title
            brand = None
            for brand_name in brand_names:
                if brand_name.lower() in new_product_name.lower():
                    brand = brand_name
                    break

            #print("Debug new_product_name: " + new_product_name)
            if re.search("^([A-G]{1,2}\d{1,4}(\/{1})?(\S{1,3}))", str(new_product_name), flags=re.IGNORECASE):
                new_product_name = move_match_to_end(str(new_product_name), "^([A-G]{1,2}\d{1,4}(\/{1})?(\S{1,3}))")
                brand = "Camon"
            if re.search("(P[A-G]{1,2}\d{1,3}-\d{3,5})", str(new_product_name), flags=re.IGNORECASE):
                new_product_name = move_match_to_end(str(new_product_name), "(P[A-G]{1,2}\d{1,3}-\d{3,5})")
                brand = "Petsafe"

            # Modify the title if brand is identified
            if brand:
                #updated_product["name"] = f"{brand} - {product_name.replace(brand, '', 1).strip()}"
                updated_product["name"] = str(brand + " - " + new_product_name.replace(brand, '', 1).strip())

            updated_product["name"] = ' '.join(updated_product["name"].split())

            # Prompt user for approval or alternative title
            print(f"Product ID: {product['id']}")
            print(f"Current Title: {product_name}")
            try:
                print(f"Updated Title: {updated_product['name']}")
                response = input("Do you want to update the title? (Y/N/S): ")
            except Exception as e:
                print(f"Could not convert title, please specify it manually or Skip")
                response = input("Do you want to update the title? (N/S): ")

            if response.lower() == 'y':
                # Update the product in WooCommerce
                createAtomicUpdateDataFile("", updated_product)
                try:
                   response = wcapi.put(f"products/{product['id']}", updated_product)
                   if response.status_code == 200:
                       print(f"Product with ID {product['id']} updated successfully.")
                       createAtomicUpdateDataFile("",
                       updateProductDataFile(file_path)
                   else:
                       print(f"Error updating product with ID {product['id']}: {response.json()}")
                except Exception as e:
                   print ("Something went wrong: " + str(e))
            elif response.lower() == 'n':
                alternative_title = input("Enter an alternative title: ")
                if alternative_title:
                    updated_product["name"] = html.escape(alternative_title)
                    response = wcapi.put(f"products/{product['id']}", updated_product)
                    if response.status_code == 200:
                        print(f"Product with ID {product['id']} updated successfully.")
                        updateProductDataFile(file_path)
                    else:
                        print(f"Error updating product with ID {product['id']}: {response.json()}")
                else:
                    print(f"No alternative title provided. Product with ID {product['id']} was not updated.")
            elif response.lower() == 's':
                print(f"Product with ID {product['id']} was skipped and not updated.")
            else:
                print(f"Invalid input. Product with ID {product['id']} was not updated.")
            print()
