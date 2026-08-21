from dotenv import load_dotenv
import os
import re
import csv

load_dotenv()

from google import genai

from backend.database.mongodb import inventory_collection
from backend.tools.inventory_tool import (
    get_inventory,
    get_low_stock_products,
    find_product,
    get_warehouse_inventory,
    get_inventory_summary,
    inventory_collection
)
from backend.tools.rag_tool import search_knowledge, rebuild_index
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import shutil
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
class InventoryProduct(BaseModel):
    product_id: str
    product_name: str
    warehouse: str
    quantity: int
    reorder_level: int

print("WMS AI Agent starting...")

app = FastAPI()
UPLOAD_DIR = Path("backend/knowledge")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


@app.get("/health")
def health_check():
    return {
        "status": "WMS AI Agent is running"
    }



@app.get("/inventory")   
def get_all_inventory():
    products = inventory_collection.find({})

    inventory = [
        {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "warehouse": product["warehouse"],
            "quantity": product["quantity"],
            "reorder_level": product["reorder_level"]
        }
        for product in products
    ]

    return {
        "inventory": inventory
    }


@app.post("/inventory/add")
def add_inventory_product(product: InventoryProduct):

    existing_product = inventory_collection.find_one({
        "product_id": product.product_id
    })

    if existing_product:
        return {
            "error": f"Product ID {product.product_id} already exists."
        }

    inventory_collection.insert_one({
        "product_id": product.product_id,
        "product_name": product.product_name,
        "warehouse": product.warehouse.upper(),
        "quantity": product.quantity,
        "reorder_level": product.reorder_level
    })

    return {
        "message": "Product added successfully.",
        "product": product.model_dump()
    }

class ChatRequest(BaseModel):
    question: str

 

@app.post("/inventory/import")
async def import_inventory_csv(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".csv"):
        return {
            "error": "Please upload a CSV file."
        }

    try:
        contents = await file.read()

        csv_text = contents.decode("utf-8")

        reader = csv.DictReader(csv_text.splitlines())

        required_columns = {
            "product_id",
            "product_name",
            "warehouse",
            "quantity",
            "reorder_level"
        }

        if not reader.fieldnames:
            return {
                "error": "CSV file has no header."
            }

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            return {
                "error": (
                    "Missing columns: "
                    + ", ".join(missing_columns)
                )
            }

        products = []

        for row in reader:

            product = {
    "product_id": row["product_id"].strip(),
    "product_name": row["product_name"].strip(),
    "warehouse": row["warehouse"].strip().upper(),
    "quantity": int(row["quantity"]),
    "reorder_level": int(row["reorder_level"]),
    "source_file": file.filename
}

            products.append(product)

        if not products:
            return {
                "error": "CSV contains no products."
            }

        inserted = 0
        skipped = 0

        for product in products:

            existing = inventory_collection.find_one({
                "product_id": product["product_id"]
            })

            if existing:
                skipped += 1
                continue

            inventory_collection.insert_one(product)
            inserted += 1

        return {
            "message": "Inventory CSV imported successfully.",
            "inserted": inserted,
            "skipped": skipped
        }

    except ValueError:
        return {
            "error": "Quantity and reorder_level must contain numbers."
        }

    except Exception as error:
        return {
            "error": f"Unable to import CSV: {str(error)}"
        }

@app.delete("/inventory/{product_id}")
def delete_inventory_product(product_id: str):

    result = inventory_collection.delete_one({
        "product_id": product_id
    })

    if result.deleted_count == 0:
        return {
            "error": "Product not found."
        }

    return {
        "message": "Product deleted successfully.",
        "product_id": product_id
    }

@app.delete("/inventory/import/{filename}")
def delete_inventory_csv(filename: str):

    result = inventory_collection.delete_many({
        "source_file": filename
    })

    return {
        "message": "Imported inventory deleted successfully.",
        "filename": filename,
        "deleted_count": result.deleted_count
    }

@app.get("/inventory/imports")
def get_inventory_imports():

    products = inventory_collection.find({
        "source_file": {
            "$exists": True
        }
    })

    files = {}

    for product in products:

        filename = product["source_file"]

        if filename not in files:
            files[filename] = 0

        files[filename] += 1

    return {
        "imports": [
            {
                "filename": filename,
                "product_count": count
            }
            for filename, count in files.items()
        ]
    }
# Products currently available in our inventory

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    allowed_extensions = {".txt", ".pdf", ".csv"}

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        return {
            "error": "Only PDF, TXT and CSV files are supported."
        }

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # --------------------------------------------------
    # CSV FILE
    # --------------------------------------------------

    if file_extension == ".csv":

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
                newline=""
            ) as csv_file:

                reader = csv.DictReader(csv_file)

                rows = list(reader)

            return {
                "message": "CSV uploaded successfully.",
                "filename": file.filename,
                "rows": len(rows),
                "columns": reader.fieldnames
            }

        except Exception as error:

            return {
                "error": f"Unable to read CSV: {str(error)}"
            }

    # --------------------------------------------------
    # PDF / TXT → RAG
    # --------------------------------------------------

    rebuild_index()

    return {
        "message": "Document uploaded successfully and added to RAG.",
        "filename": file.filename
    }


@app.get("/documents")
def get_documents():

    documents = []

    for file_path in UPLOAD_DIR.iterdir():

        if file_path.is_file() and file_path.suffix.lower() in {
            ".txt",
            ".pdf",
            ".csv"
        }:

            extension = file_path.suffix.lower()

            if extension == ".csv":
                document_type = "CSV"
            elif extension == ".pdf":
                document_type = "PDF"
            else:
                document_type = "TXT"

            documents.append({
                "filename": file_path.name,
                "type": document_type
            })

    return {
        "documents": documents
    }
@app.delete("/documents/{filename}")
def delete_document(filename: str):

    file_path = UPLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        return {
            "error": "Document not found."
        }

    file_path.unlink()

    # Rebuild RAG index after deleting a document
    rebuild_index()

    return {
        "message": "Document deleted successfully.",
        "filename": filename
    }

@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()
    question_lower = question.lower()

    warehouse_match = re.search(r'\bW\d+\b', question, re.IGNORECASE)

    if warehouse_match:
        warehouse = warehouse_match.group().upper()

        result = get_warehouse_inventory(warehouse)

        if not result:
            return {
                "question": question,
                "answer": f"No inventory found for warehouse {warehouse}.",
                "warehouse": warehouse,
                "inventory": []
            }

        return {
            "question": question,
            "answer": f"Warehouse {warehouse} has {len(result)} products.",
            "warehouse": warehouse,
            "inventory": result
        }
        # --------------------------------------------------
    # INVENTORY SUMMARY
    # --------------------------------------------------

    if (
        "total inventory" in question_lower
        or "total stock" in question_lower
        or "overall inventory" in question_lower
        or "overall stock" in question_lower
        or "how many units are in stock overall" in question_lower
    ):
        result = get_inventory_summary()

        return {
            "question": question,
            "answer": (
                f"We have {result['total_quantity']} units across "
                f"{result['total_products']} products. "
                f"{result['low_stock_products']} products are low on stock."
            ),
            "inventory_summary": result
        }
    # --------------------------------------------------
    # 1. FIRST: CHECK IF A SPECIFIC PRODUCT WAS MENTIONED
    # --------------------------------------------------

    selected_product = find_product(question)

    if selected_product:

        result = get_inventory(selected_product)

        if result is None:
            return {
                "question": question,
                "message": "Product not found in inventory."
            }

        is_low_stock = (
            result["quantity"] < result["reorder_level"]
        )

        # --------------------------------------------------
        # PRODUCT-SPECIFIC LOW STOCK QUESTION
        # --------------------------------------------------

        if (
            "low stock" in question_lower
            or "low on stock" in question_lower
            or "running low" in question_lower
            or "enough" in question_lower
            or "reorder" in question_lower
        ):

            if is_low_stock:
                answer = (
                    f"Yes. {result['product_name']} has "
                    f"{result['quantity']} units available, "
                    f"which is below the reorder level of "
                    f"{result['reorder_level']}."
                )
            else:
                answer = (
                    f"Yes. {result['product_name']} has "
                    f"{result['quantity']} units available, "
                    f"which is above the reorder level of "
                    f"{result['reorder_level']}."
                )

            return {
                "question": question,
                "answer": answer,
                "inventory": result,
                "low_stock": is_low_stock
            }

        # --------------------------------------------------
        # NORMAL PRODUCT QUESTION
        # --------------------------------------------------

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"""
Answer the user's inventory question using ONLY
the inventory data below.

Inventory data:
{result}

User question:
{question}

Rules:
- Do not invent information.
- Keep the answer short and clear.
- Mention the quantity when relevant.
- If stock is below the reorder level, mention that
  the product is low on stock.
"""
            )

            answer = response.text

        except Exception:

            answer = (
                f"There are {result['quantity']} units of "
                f"{result['product_name']} available."
            )

            if is_low_stock:
                answer += (
                    f" This is below the reorder level of "
                    f"{result['reorder_level']}, so it is low on stock."
                )

        return {
            "question": question,
            "answer": answer,
            "inventory": result,
            "low_stock": is_low_stock
        }

    # --------------------------------------------------
    # 2. NO SPECIFIC PRODUCT → GENERAL LOW STOCK QUESTION
    # --------------------------------------------------

    if (
        "low stock" in question_lower
        or "low on stock" in question_lower
        or "running low" in question_lower
        or "need to be reordered" in question_lower
        or "need reorder" in question_lower
        
    ):

        result = get_low_stock_products()

        if not result:
            return {
                "question": question,
                "answer": "All products currently have sufficient stock.",
                "low_stock_products": []
            }

        product_names = [
            product["product_name"]
            for product in result
        ]

        answer = (
            f"{len(result)} products need attention: "
            + ", ".join(product_names)
            + "."
        )

        return {
            "question": question,
            "answer": answer,
            "low_stock_products": result
        }
         # --------------------------------------------------
    # 3. KNOWLEDGE QUESTION → RAG
    # --------------------------------------------------

    retrieved_docs = search_knowledge(question)

    if retrieved_docs:
        context = "\n\n".join(
            document["text"]
            for document in retrieved_docs
        )

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"""
Answer the user's question using ONLY the retrieved
documents below.

Retrieved documents:
{context}

User question:
{question}

Rules:
- Do not invent information.
- Use only information present in the retrieved documents.
- If the answer is not present, say you could not find it
  in the uploaded documents.
- Keep the answer clear and concise.
"""
            )

            answer = response.text

        except Exception:
            answer = context

        return {
            "question": question,
            "answer": answer,
            "rag": True,
            "sources": [
                document["source"]
                for document in retrieved_docs
            ]
        }

    # --------------------------------------------------
    # 4. UNKNOWN QUESTION
    # --------------------------------------------------

    return {
        "question": question,
        "message": "I couldn't find relevant information for this question."
    }