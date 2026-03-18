from fastapi import FastAPI, HTTPException, Response, status, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# — Existing Data ———————————————————————————————————————
products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',       'price': 99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False },
    {'id': 4, 'name': 'Pen Set',        'price': 49,  'category': 'Stationery',  'in_stock': True },
]

# — Pydantic Model for New Products ——————————————————————
class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str
    in_stock: bool = True

# — GET: All Products ————————————————————————————————————
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

# — POST: Add New Product ————————————————————————————————
@app.post("/products", status_code=201)
def add_product(item: NewProduct):
    # Check for duplicates (Case-insensitive)
    for p in products:
        if p["name"].lower() == item.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
    
    # Auto-generate ID (Max ID + 1)
    new_id = max([p['id'] for p in products]) + 1 if products else 1
    
    new_product = item.dict()
    new_product["id"] = new_id
    
    products.append(new_product)
    
    return {
        "message": "Product added",
        "product": new_product
    }

# — 1. GET: Inventory Audit (AGGREGATION) —
# CRITICAL: Must be ABOVE the {product_id} path parameter route
@app.get('/products/audit')
def product_audit():
    # Filter lists for stock status
    in_stock_list = [p for p in products if p['in_stock']]
    out_stock_list = [p for p in products if not p['in_stock']]
    
    # Calculation: Sum of (price * 10) for all items where in_stock is True
    stock_value = sum(p['price'] * 10 for p in in_stock_list)
    
    # Logic: Find the highest priced item in the entire list
    priciest = max(products, key=lambda p: p['price'])
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p['name'] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {
            "name": priciest['name'],
            "price": priciest['price']
        }
    }

# — 1. PUT: Bulk Category Discount —
# Place this above /{product_id} so "discount" isn't mistaken for an ID
@app.put('/products/discount')
def bulk_discount(
    category: str = Query(..., description='Category to apply discount to'),
    discount_percent: int = Query(..., ge=1, le=99, description='Percentage to cut (1-99)')
):
    updated_products = []
    
    for p in products:
        # Case-insensitive category matching
        if p['category'].lower() == category.lower():
            # Calculate new price and convert to int to avoid decimal prices
            discount_multiplier = 1 - (discount_percent / 100)
            p['price'] = int(p['price'] * discount_multiplier)
            updated_products.append(p)
            
    if not updated_products:
        return {'message': f'No products found in category: {category}'}
        
    return {
        'message': f'{discount_percent}% discount applied to {category}',
        'updated_count': len(updated_products),
        'updated_products': updated_products
    }

# — GET: Single Product ——————————————————————————————————
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# — PUT: Update Product (Restock Logic) ——————————————————
@app.put("/products/{product_id}")
def update_product(
    product_id: int, 
    price: Optional[int] = Query(None, gt=0), 
    in_stock: Optional[bool] = Query(None)
):
    # 1. Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. Update price (only if the user sent a value)
    if price is not None:
        product["price"] = price
        
    # 3. Update stock (CRITICAL: checks if the parameter exists at all)
    if in_stock is not None:
        product["in_stock"] = in_stock
        
    return {
        "message": f"Product {product_id} updated successfully",
        "product": product
    }

# — Helper function to find a product ————————————————————
def find_product(product_id: int):
    return next((p for p in products if p["id"] == product_id), None)

# — DELETE: Remove a Product —————————————————————————————
@app.delete('/products/{product_id}')
def delete_product(product_id: int, response: Response):
    # Step 1: Attempt to find the product
    product = find_product(product_id)
    
    # Step 2: If it doesn't exist, return 404
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
    
    # Step 3: Remove it from the list
    products.remove(product)
    
    # Step 4: Return confirmation with the deleted product's name
    return {'message': f"Product '{product['name']}' deleted"}

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str
    in_stock: bool = True

# — 1. POST: Create —
@app.post("/products", status_code=201)
def add_product(item: NewProduct):
    new_id = max([p['id'] for p in products]) + 1 if products else 1
    new_product = item.dict()
    new_product["id"] = new_id
    products.append(new_product)
    return {"message": "Product added", "product": new_product}

# — 2. GET: Read All —
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

# — 3. PUT: Update —
@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = Query(None, gt=0)):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if price is not None:
        product["price"] = price
    return {"message": "Price updated", "product": product}

# — 4. DELETE: Remove —
@app.delete('/products/{product_id}')
def delete_product(product_id: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}