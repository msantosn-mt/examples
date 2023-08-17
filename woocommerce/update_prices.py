# -*- coding: utf-8 -*-
import sys, os
import pandas as pd
from time import sleep
from woocommerce import API

if len(sys.argv) != 5:
   print ("Need to specify the CSV file (pricelist), the column name with the SKU, the column name with the price, and the column name with the status.\n\n")
   print ("Example: " + str(sys.argv[0]) + " <Pricelist File> '<SKU Column name>' '<Price Column name>' '<Notes column name>\n", )
   print ("Example: " + str(sys.argv[0]) + " input.csv 'SKU' 'Public Price' 'Notes'\n", )
   exit(1)

csvFile = sys.argv[1]
skuColumn = sys.argv[2]
priceColumn = sys.argv[3]
notesColumn = sys.argv[4]

try:
    df = pd.read_csv(csvFile, sep=',', keep_default_na=False)
except Exception as e:
    print ("Could not load the CSV file: " + csvFile + ": " + str(e))
    sys.exit(1)
    
if notesColumn not in df.columns:
    # Create the new column with default values
    df[notesColumn] = None
    print ("Created new Column: " + notesColumn)

wcapi = API(
    url="url",
    consumer_key="replaceme",
    consumer_secret="replaceme",
    version="wc/v3"
)

def get_product_by_sku(itemSKU):
   response = wcapi.get("products",params={"sku": itemSKU}).json()
   if response:
      return response
   else:
      return ''

def update_product_price(product_id,parent_id,newItemPrice):
   updated_data = {
     "regular_price": str(newItemPrice)
   }
   # If parent_id is not zero, it is variable product.
   if parent_id == 0:
      request_resource = str("products/" + str(product_id))
   else:
      request_resource = str("products/" + str(parent_id) + "/variations/" + str(product_id))
   response = wcapi.put(request_resource, updated_data)
   return response

# Iterate over each row
for index, row in df.iterrows():
   updated_notes = []
   try:
      itemSKU = str(row[skuColumn])
      newItemPrice = float(row[priceColumn])
      itemNotes = str(row[notesColumn])
   except Exception as e:
      print ("\nCould not values from CSV : " + str(index) + ": " + str(e))
      continue

   response = get_product_by_sku(itemSKU)
   if len(response) == 1:
      item = response[0]
      product_id = int(item['id'])
      parent_id = int(item['parent_id'])
      try:
         regular_price = float(item['regular_price'])
      except Exception as e:
         updated_notes.append("NoValidOriginalRegularPriceInDB")
         regular_price = float('0.00')
      if newItemPrice == regular_price:
         updated_notes.append("SamePriceNotUpdated")
      else:
         if newItemPrice < regular_price:
            updated_notes.append("NewPriceCheaperWAS:" + str(regular_price))

         response_update = update_product_price(product_id,parent_id,newItemPrice)
      
         if response_update.status_code != 200:
            updated_notes.append("ErrorUpdatingError:" + str(response_update.status_code))
         else:
            updated_notes.append("SUCCESS")

   elif len(response) == 0:
      updated_notes.append("SKUNotFoundInDB")
   else:
      updated_notes.append("MultipleSKUsInDB")

   updated_notes_string = '|'.join(updated_notes)
   print("SKU: " + itemSKU + ", Notes: " + updated_notes_string)
   df.at[index, notesColumn] = updated_notes_string
   df.to_csv(csvFile + "-new.csv", sep=',', index=False)
   sleep(1)
