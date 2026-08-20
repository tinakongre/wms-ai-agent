import sys
sys.path.append("backend")
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def get_inventory(product_name: str):
    from tools.inventory_tool import get_inventory as db_get_inventory

    return db_get_inventory(product_name)

tools = [get_inventory]
chat = client.chats.create(
    model="gemini-3.6-flash",
    config={
        "tools": [{"function_declarations": [{
            "name": "get_inventory",
            "description": "Find the current inventory details of a product in the warehouse.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "product_name": {
                        "type": "STRING",
                        "description": "The exact or partial product name to search for."
                    }
                },
                "required": ["product_name"]
            }
        }]}]
    }
)
question = input("You: ")

response = chat.send_message(question)

function_call = response.candidates[0].content.parts[0].function_call

if function_call:
    result = get_inventory(function_call.args["product_name"])

print(
    f"{result['product_name']}: {result['quantity']} units available "
    f"at warehouse {result['warehouse']}."
)