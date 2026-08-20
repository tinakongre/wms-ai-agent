from backend.database.mongodb import inventory_collection


inventory = [
    {
        "product_id": "P001",
        "product_name": "Wireless Keyboard",
        "warehouse": "W01",
        "quantity": 120,
        "reorder_level": 50
    },
    {
        "product_id": "P002",
        "product_name": "Wireless Mouse",
        "warehouse": "W01",
        "quantity": 75,
        "reorder_level": 40
    },
    {
        "product_id": "P003",
        "product_name": "LED Monitor",
        "warehouse": "W02",
        "quantity": 25,
        "reorder_level": 30
    },
    {
        "product_id": "P004",
        "product_name": "Mechanical Keyboard",
        "warehouse": "W03",
        "quantity": 15,
        "reorder_level": 50
    },
    {
        "product_id": "P005",
        "product_name": "Laptop Stand",
        "warehouse": "W02",
        "quantity": 60,
        "reorder_level": 20
    }
]


inventory_collection.delete_many({})

result = inventory_collection.insert_many(inventory)

print(f"Inserted {len(result.inserted_ids)} inventory records.")