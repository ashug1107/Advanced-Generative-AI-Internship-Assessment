from fastapi import FastAPI, Query

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

# — Endpoint 0 - Home ————————————————————————————————————
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

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

# — Endpoint 7 - Advanced Filter (Query Parameters) ———————
@app.get('/products/filter')
def filter_products(
    category: str = Query(None, description='Electronics or Stationery'),
    max_price: int = Query(None, description='Maximum price'),
    in_stock: bool = Query(None, description='True = in stock only')
):
    result = products
    
    if category:
        result = [p for p in result if p['category'] == category]
        
    if max_price:
        result = [p for p in result if p['price'] <= max_price]
        
    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]
        
    return {'filtered_products': result, 'count': len(result)}