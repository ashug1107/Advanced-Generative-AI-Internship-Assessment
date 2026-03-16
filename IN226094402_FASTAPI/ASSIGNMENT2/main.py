from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# — Temporary data – acting as our database for now ——————
products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',       'price': 99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False },
    {'id': 4, 'name': 'Pen Set',        'price': 49,  'category': 'Stationery',  'in_stock': True },
    # ➕ Added 3 new products below
    {'id': 5, 'name': 'Gaming Keyboard','price': 1200, 'category': 'Electronics', 'in_stock': True },
    {'id': 6, 'name': 'Desk Lamp',      'price': 350,  'category': 'Home Office', 'in_stock': True },
    {'id': 7, 'name': 'Water Bottle',   'price': 150,  'category': 'Accessories', 'in_stock': False },
]

# This list will store our feedback objects
feedback_list = []

# — Pydantic Model with Validation Rules —————————————————
class CustomerFeedback(BaseModel):
    # customer_name: must be at least 2 characters
    customer_name: str = Field(..., min_length=2, max_length=100)
    
    # product_id: must be greater than 0
    product_id: int = Field(..., gt=0)
    
    # rating: must be between 1 and 5 (inclusive)
    rating: int = Field(..., ge=1, le=5)
    
    # comment: optional, maximum 300 characters
    comment: Optional[str] = Field(None, max_length=300)

# — Endpoint: Submit Feedback ————————————————————————————
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    # Convert the Pydantic model to a dictionary
    feedback_entry = data.dict()
    
    # Save to our temporary list
    feedback_list.append(feedback_entry)
    
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback_entry,
        "total_feedback": len(feedback_list)
    }

# — Pydantic Models for Bulk Orders ——————————————————————
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

# — Endpoint: Bulk Order Placement ———————————————————————
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    
    for item in order.items:
        # Find the product by ID
        product = next((p for p in products if p["id"] == item.product_id), None)
        
        # Scenario A: Product doesn't exist
        if not product:
            failed.append({
                "product_id": item.product_id, 
                "reason": "Product ID not found in our catalog"
            })
        
        # Scenario B: Product is out of stock
        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id, 
                "reason": f"{product['name']} is currently out of stock"
            })
            
        # Scenario C: Success
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })
            
    return {
        "company": order.company_name,
        "contact": order.contact_email,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# Global list to store orders
orders = []

# — Pydantic Models ——————————————————————————————————————
class OrderRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)

# — Endpoint 1: Place Order (Starts as Pending) ——————————
@app.post("/orders")
def place_order(request: OrderRequest):
    # Check if product exists
    product = next((p for p in products if p["id"] == request.product_id), None)
    if not product:
        return {"error": "Product not found"}
    
    # Create the order object
    new_order = {
        "order_id": len(orders) + 1,
        "product_name": product["name"],
        "quantity": request.quantity,
        "total_price": product["price"] * request.quantity,
        "status": "pending"  # ✏️ Default status is now pending
    }
    
    orders.append(new_order)
    return {"message": "Order placed", "order": new_order}

# — Endpoint 2: Get Order by ID ——————————————————————————
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    # Find order in our list
    order = next((o for o in orders if o["order_id"] == order_id), None)
    
    if not order:
        return {"error": "Order not found"}
    
    return {"order": order}

# — Endpoint 3: Confirm Order (PATCH Update) ——————————————
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    # Find the specific order
    for order in orders:
        if order["order_id"] == order_id:
            # Check if it's already confirmed (optional logic)
            if order["status"] == "confirmed":
                return {"message": "Order is already confirmed"}
            
            # Update the status
            order["status"] = "confirmed"
            return {"message": "Order status updated to confirmed", "order": order}
            
    return {"error": "Order not found"}

# — Endpoint 0 - Home ————————————————————————————————————
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

# — Endpoint: Product Summary Dashboard —————————————————
@app.get("/products/summary")
def product_summary():
    # 1. Filter lists for stock counts
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]
    
    # 2. Find expensive and cheapest items
    expensive_item = max(products, key=lambda p: p["price"])
    cheapest_item = min(products, key=lambda p: p["price"])
    
    # 3. Get unique categories
    categories_list = list(set(p["category"] for p in products))
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_count": len(out_stock_list),
        "most_expensive": {
            "name": expensive_item["name"], 
            "price": expensive_item["price"]
        },
        "cheapest": {
            "name": cheapest_item["name"], 
            "price": cheapest_item["price"]
        },
        "categories": categories_list
    }

# — Endpoint 1 - Deals (Cheapest & Most Expensive) ————————
@app.get("/products/deals")
def get_deals():
    # min() finds the item with the lowest value based on the 'price' key
    cheapest = min(products, key=lambda p: p["price"])
    
    # max() finds the item with the highest value based on the 'price' key
    expensive = max(products, key=lambda p: p["price"])
    
    return {
        "best_deal": cheapest, 
        "premium_pick": expensive
    }

# — Endpoint 2 - Store Summary ———————————————————————————
@app.get("/store/summary")
def store_summary():
    # Calculate counts using list comprehensions
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    
    # Get unique categories using set()
    # set() automatically removes duplicates
    categories = list(set([p["category"] for p in products]))
    
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

# — Endpoint 3 - Return all products —————————————————————
@app.get('/products')
def get_all_products():
    # len(products) will now dynamically return 7
    return {'products': products, 'total': len(products)}

# — Endpoint 4 - Search Products by Name —————————————————
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    # Using .lower() on both sides makes the search case-insensitive
    results = [
        p for p in products 
        if keyword.lower() in p["name"].lower()
    ]
    
    if not results:
        return {"message": "No products matched your search"}
        
    return {
        "keyword": keyword, 
        "results": results, 
        "total_matches": len(results)
    }

# — Endpoint 5 - Show Only In-Stock Products ——————————————
@app.get("/products/instock")
def get_instock():
    # Filter only where in_stock is True
    available = [p for p in products if p["in_stock"] == True]
    
    return {
        "in_stock_products": available,
        "count": len(available)
    }

# — Endpoint 6 - Category Filter (Path Parameter) —————————
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    # Filter products where category matches the path parameter
    result = [p for p in products if p["category"].lower() == category_name.lower()]
    
    # Check if the result list is empty
    if not result:
        return {"error": "No products found in this category"}
    
    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }

# — Endpoint 7 - Get Product Price Only (Path Parameter) ———
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            # We construct a new dictionary with only 2 keys
            return {
                "name": product["name"], 
                "price": product["price"]
            }
    
    # If the loop finishes without finding the ID
    return {"error": "Product not found"}

# — Endpoint 8 - Advanced Filter (Query Parameters) ———————
@app.get('/products/filter')
def filter_products(
    category: str = Query(None, description='Electronics or Stationery'),
    min_price: int = Query(None, description='Minimum price'), # ➕ Added parameter
    max_price: int = Query(None, description='Maximum price'),
    in_stock: bool = Query(None, description='True = in stock only')
):
    result = products
    
    if category:
        result = [p for p in result if p['category'] == category]

    if min_price: # ➕ New filter logic
        result = [p for p in result if p['price'] >= min_price]
        
    if max_price:
        result = [p for p in result if p['price'] <= max_price]
        
    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]
        
    return {'filtered_products': result, 'count': len(result)}