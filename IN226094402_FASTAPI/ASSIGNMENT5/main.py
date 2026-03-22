from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Sample Database
products = [
    {"id": 1, "name": "Wireless Mouse"},
    {"id": 2, "name": "Keyboard"},
    {"id": 3, "name": "Monitor"},
    {"id": 4, "name": "Webcam"}
]

@app.get("/products/search")
async def search_products(keyword: str):
    # 1. The 'One-Liner' logic: filter products by case-insensitive keyword
    results = [p for p in products if keyword.lower() in p['name'].lower()]
    
    # 2. Handle the "laptop" case: if no results, return a custom message
    if not results:
        return {"message": f"No products found for: {keyword}"}
    
    # 3. Return the results and the count
    return {
        "results": results,
        "total_found": len(results)
    }

@app.get("/products/sort")
async def sort_products(
    sort_by: str = "price", 
    order: str = "asc"
):
    # 1. Validation: Reject invalid sort fields
    if sort_by not in ["price", "name"]:
        raise HTTPException(
            status_code=400, 
            detail="Error: sort_by must be 'price' or 'name'"
        )

    # 2. Determine Sort Direction
    # If order is 'desc', reverse is True. Otherwise, it's False.
    is_reverse = (order == "desc")

    # 3. Apply the sorting logic
    # key=lambda p: p[sort_by] tells Python which dictionary key to compare
    sorted_list = sorted(
        products, 
        key=lambda p: p[sort_by], 
        reverse=is_reverse
    )

    # 4. Return the sorted list along with the parameters used
    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_list
    }

@app.get("/products/page")
async def get_products_page(page: int = 1, limit: int = 2):
    # 1. Calculate the Start and End indices for the slice
    # Page 1 starts at 0, Page 2 starts at 2, etc.
    start = (page - 1) * limit
    end = start + limit
    
    # 2. Slice the list
    # Python lists safely return an empty list [] if indices are out of range
    paged_products = products[start:end]
    
    # 3. Calculate total pages (Ceiling Division)
    # This formula rounds up. Example: 4 // 2 = 2. But 5 // 2 = 3.
    total_pages = -(-len(products) // limit)
    
    # 4. Return the response
    return {
        "page": page,
        "limit": limit,
        "total_items": len(products),
        "total_pages": total_pages,
        "products": paged_products
    }

# 1. Database and Schema
orders = []  # Our temporary in-memory database

class Order(BaseModel):
    order_id: int
    customer_name: str
    items: List[str]
    total_amount: float

# 2. Task: Create orders so we have data to search
@app.post("/orders", status_code=201)
async def create_order(order: Order):
    orders.append(order.dict())
    return {"message": "Order placed successfully", "order": order}

# 3. Task: Build the Search Endpoint
@app.get("/orders/search")
async def search_orders(customer_name: str = Query(..., description="The name to search for")):
    # Case-insensitive partial match logic
    results = [
        o for o in orders 
        if customer_name.lower() in o['customer_name'].lower()
    ]
    
    # 4. Task: Handle "No Results" case
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    
    # 5. Return the requested response format
    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }

@app.get("/products/sort-by-category")
async def sort_by_category():
    # The Tuple Key Logic:
    # Python compares p['category'] first (Alphabetical A-Z)
    # Then compares p['price'] second (Numerical Low-High)
    result = sorted(products, key=lambda p: (p['category'], p['price']))
    
    return {
        "status": "success",
        "total": len(result),
        "products": result
    }

@app.get("/products/browse")
async def browse_products(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20)
):
    # --- STEP 1: FILTERING ---
    # We start with the full list and narrow it down if a keyword exists
    filtered_results = products
    if keyword:
        filtered_results = [
            p for p in products 
            if keyword.lower() in p['name'].lower()
        ]

    # --- STEP 2: SORTING ---
    # Sort the filtered list before we cut it into pages
    is_reverse = (order == "desc")
    if sort_by in ["price", "name"]:
        filtered_results = sorted(
            filtered_results, 
            key=lambda p: p[sort_by], 
            reverse=is_reverse
        )

    # --- STEP 3: PAGINATION ---
    total_found = len(filtered_results)
    start = (page - 1) * limit
    end = start + limit
    paged_results = filtered_results[start:end]
    
    total_pages = -(-total_found // limit) if total_found > 0 else 0

    return {
        "metadata": {
            "keyword_used": keyword,
            "sort_by": sort_by,
            "order": order,
            "page": page,
            "limit": limit,
            "total_found": total_found,
            "total_pages": total_pages
        },
        "products": paged_results
    }

# In-memory database for orders
orders = []

@app.get("/orders/page")
async def get_orders_paged(
    page: int = Query(1, ge=1), 
    limit: int = Query(3, ge=1, le=50)
):
    # 1. Calculate the 'window' indices
    start = (page - 1) * limit
    end = start + limit
    
    # 2. Slice the orders list
    # If page=1, limit=3: orders[0:3]
    # If page=2, limit=3: orders[3:6]
    paged_orders = orders[start:end]
    
    # 3. Calculate metrics
    total_items = len(orders)
    # Ceiling division to handle leftover items on the last page
    total_pages = -(-total_items // limit) if total_items > 0 else 0
    
    return {
        "metadata": {
            "current_page": page,
            "items_per_page": limit,
            "total_orders": total_items,
            "total_pages": total_pages
        },
        "orders": paged_orders
    }