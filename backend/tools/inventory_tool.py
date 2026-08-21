from backend.database.mongodb import inventory_collection

def get_inventory(product_name):
    product = inventory_collection.find_one({
        "product_name": {
            "$regex": product_name,
            "$options": "i"
        }
    })

    if not product:
        return None

    return {
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "warehouse": product["warehouse"],
        "quantity": product["quantity"],
        "reorder_level": product["reorder_level"]
    }
def get_low_stock_products():
    products = inventory_collection.find({
        "$expr": {
            "$lt": ["$quantity", "$reorder_level"]
        }
    })

    return [
        {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "warehouse": product["warehouse"],
            "quantity": product["quantity"],
            "reorder_level": product["reorder_level"]
        }
        for product in products
    ]
if __name__ == "__main__":
    print(get_low_stock_products())

def find_product(question):
    question = question.lower()

    products = inventory_collection.find(
        {},
        {"product_name": 1}
    )

    for product in products:
        product_name = product["product_name"]
        product_lower = product_name.lower()

        # Exact product name
        if product_lower in question:
            return product_name

        # Simple plural handling
        if product_lower + "s" in question:
            return product_name

    return None
def get_warehouse_inventory(warehouse):
    products = inventory_collection.find({
        "warehouse": warehouse.upper()
    })

    return [
        {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "warehouse": product["warehouse"],
            "quantity": product["quantity"],
            "reorder_level": product["reorder_level"]
        }
        for product in products
    ]
def get_inventory_summary():
    products = inventory_collection.find({})

    total_products = 0
    total_quantity = 0
    low_stock_count = 0

    for product in products:
        total_products += 1
        total_quantity += product["quantity"]

        if product["quantity"] < product["reorder_level"]:
            low_stock_count += 1

    return {
        "total_products": total_products,
        "total_quantity": total_quantity,
        "low_stock_products": low_stock_count
    }
def get_all_inventory():
    products = inventory_collection.find({})

    return [
        {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "warehouse": product["warehouse"],
            "quantity": product["quantity"],
            "reorder_level": product["reorder_level"]
        }
        for product in products
    ]