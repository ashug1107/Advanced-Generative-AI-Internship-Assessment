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

# — 2. Temporary Cart Storage ————————————————————————————
cart = []

# — 3. Endpoint: Add to Cart —————————————————————————————
@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., gt=0, description="The ID of the product"),
    quantity: int = Query(..., ge=1, description="Number of items to add")
):
    # Find the product in our database
    product = next((p for p in products if p["id"] == product_id), None)
    
    # Validation: Does the product exist?
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Calculate the subtotal (Price × Quantity)
    subtotal = product["price"] * quantity
    
    # Create the cart item object
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": subtotal
    }
    
    # Add to our cart list
    cart.append(cart_item)
    
    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }

# — 4. Helper Endpoint: View Cart ————————————————————————
@app.get("/cart")
def view_cart():
    total_bill = sum(item["subtotal"] for item in cart)
    return {"items": cart, "total_bill": total_bill}

# — 2. GET: View Cart and Summary —————————————————————————
@app.get("/cart")
def view_cart():
    # item_count is the number of unique product entries in the list
    item_count = len(cart)
    
    # grand_total is the sum of every 'subtotal' field in the cart
    grand_total = sum(item[ "subtotal"] for item in cart)
    
    return {
        "items": cart,
        "item_count": item_count,
        "grand_total": grand_total
    }

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    # 1. Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    
    # 2. Check: Does it exist? (404 Error)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 3. Check: Is it in stock? (400 Error)
    if not product["in_stock"]:
        raise HTTPException(
            status_code=400, 
            detail=f"{product['name']} is out of stock"
        )
    
    # 4. Success: Add to cart
    subtotal = product["price"] * quantity
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "subtotal": subtotal
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    # 1. Find the product in the master database
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # 2. DUPLICATE CHECK: Is this product already in the cart?
    for item in cart:
        if item["product_id"] == product_id:
            # Update existing item
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["unit_price"]
            
            return {
                "message": "Cart updated", 
                "cart_item": item
            }

    # 3. If NOT in cart, create a new entry (Normal Flow)
    subtotal = product["price"] * quantity
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": subtotal
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}

orders = []      # NEW: Persistent order history

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# — 1. DELETE: Remove from Cart ————————————————————————
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    global cart
    # Find the item in the cart
    item = next((i for i in cart if i["product_id"] == product_id), None)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    
    cart.remove(item)
    return {"message": f"Removed {item['product_name']} from cart"}

# — 2. POST: Checkout ——————————————————————————————————
@app.post("/cart/checkout")
def checkout(details: CheckoutRequest):
    global cart
    if not cart:
        raise HTTPException(status_code=400, detail="Cannot checkout an empty cart")
    
    # Calculate final totals
    total_price = sum(item["subtotal"] for item in cart)
    
    # Create the order record
    new_order = {
        "order_id": len(orders) + 1,
        "customer": details.customer_name,
        "address": details.delivery_address,
        "items": list(cart), # Copy current cart items
        "total_price": total_price
    }
    
    orders.append(new_order)
    
    # CRITICAL: Empty the cart after successful checkout
    cart.clear()
    
    return {
        "message": "Order placed successfully!", 
        "order_details": new_order
    }

# — 3. GET: View Orders ————————————————————————————————
@app.get("/orders")
def get_orders():
    return {"orders_placed": orders, "total_orders": len(orders)}


class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# — 1. ADD TO CART (Logic from Task 4) —
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product or not product["in_stock"]:
        raise HTTPException(status_code=400, detail="Invalid product or out of stock")
    
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * product["price"]
            return {"message": "Cart updated", "cart_item": item}

    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}

# — 2. CHECKOUT (Logic: One Order Per Item) —
@app.post("/cart/checkout")
def checkout(details: CheckoutRequest):
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Create an individual order for EACH item in the cart
    for item in cart:
        new_order = {
            "order_id": len(orders) + 1,
            "customer_name": details.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"]
        }
        orders.append(new_order)
    
    cart.clear() # Clear cart for next customer
    return {"message": f"Checkout complete for {details.customer_name}"}

# — 3. VIEW ORDERS —
@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}

# — 4. DELETE & GET CART (Standard) —
@app.delete("/cart/{product_id}")
def delete_item(product_id: int):
    global cart
    cart = [item for item in cart if item["product_id"] != product_id]
    return {"message": "Item removed"}

@app.get("/cart")
def get_cart():
    return {"items": cart, "grand_total": sum(i["subtotal"] for i in cart)}

@app.post("/cart/checkout")
def checkout(details: CheckoutRequest):
    # — THE GUARD CLAUSE —
    # Check if the cart is empty BEFORE doing anything else
    if len(cart) == 0:
        raise HTTPException(
            status_code=400, 
            detail="Cart is empty — add items first before checking out"
        )
    
    # ... rest of your checkout logic (this only runs if the cart is NOT empty) ...
    for item in cart:
        new_order = {
            "order_id": len(orders) + 1,
            "customer_name": details.customer_name,
            "product": item["product_name"],
            "total_price": item["subtotal"]
        }
        orders.append(new_order)
    
    cart.clear()
    return {"message": "Checkout successful"}