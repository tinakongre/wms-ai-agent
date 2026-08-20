from dotenv import load_dotenv
import os
import re

load_dotenv()

from google import genai
from backend.tools.inventory_tool import (
    get_inventory,
    get_low_stock_products,
    find_product,
    get_warehouse_inventory,
    get_inventory_summary
)
from backend.tools.rag_tool import search_knowledge
from fastapi import FastAPI
from pydantic import BaseModel

print("WMS AI Agent starting...")

app = FastAPI()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


@app.get("/health")
def health_check():
    return {
        "status": "WMS AI Agent is running"
    }


class ChatRequest(BaseModel):
    question: str


# Products currently available in our inventory






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

    rag_keywords = [
        "policy",
        "procedure",
        "guideline",
        "when should",
        "how should",
        "warehouse rule",
        "reorder policy"
    ]

    if any(keyword in question_lower for keyword in rag_keywords):

        retrieved_docs = search_knowledge(question)

        if not retrieved_docs:
            return {
                "question": question,
                "message": "I couldn't find relevant information."
            }

        context = "\n\n".join(
            document["text"]
            for document in retrieved_docs
        )

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"""
Answer the user's question using ONLY the retrieved
warehouse knowledge below.

Retrieved knowledge:
{context}

User question:
{question}

Rules:
- Do not invent information.
- Answer using only the retrieved knowledge.
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
    # 3. UNKNOWN QUESTION / PRODUCT
    # --------------------------------------------------

    return {
        "question": question,
        "message": "I couldn't identify a product in your question."
    }