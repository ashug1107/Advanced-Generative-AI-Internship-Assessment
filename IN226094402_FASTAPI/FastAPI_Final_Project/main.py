from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Grand Stay Hotel Management System")

# --- DATABASE SETUP (Day 1) ---
rooms_db = [
    {"id": 1, "room_number": "101", "type": "Single", "price_per_night": 1000, "floor": 1, "is_available": True},
    {"id": 2, "room_number": "102", "type": "Double", "price_per_night": 2000, "floor": 1, "is_available": True},
    {"id": 3, "room_number": "201", "type": "Suite", "price_per_night": 5000, "floor": 2, "is_available": True},
    {"id": 4, "room_number": "202", "type": "Deluxe", "price_per_night": 3500, "floor": 2, "is_available": True},
    {"id": 5, "room_number": "301", "type": "Suite", "price_per_night": 5500, "floor": 3, "is_available": True},
    {"id": 6, "room_number": "302", "type": "Single", "price_per_night": 1200, "floor": 3, "is_available": True},
]

# --- DAY 2: PYDANTIC MODELS (Validation & Field Constraints) ---
class BookingRequest(BaseModel):
    guest_name: str = Field(..., min_length=2)
    room_id: int = Field(..., gt=0)
    nights: int = Field(..., gt=0, le=30)
    phone: str = Field(..., min_length=10)
    meal_plan: str = "none" 
    early_checkout: bool = False

class NewRoom(BaseModel):
    room_number: str = Field(..., min_length=1)
    type: str = Field(..., min_length=2)
    price_per_night: int = Field(..., gt=0)
    floor: int = Field(..., gt=0)
    is_available: bool = True

# --- DAY 3: HELPER FUNCTIONS ---
def find_room(room_id: int):
    return next((r for r in rooms_db if r["id"] == room_id), None)

def calculate_stay_cost(price: int, nights: int, meal_plan: str, early_checkout: bool):
    meal_prices = {"none": 0, "breakfast": 500, "all-inclusive": 1200}
    base_price = (price + meal_prices.get(meal_plan.lower(), 0)) * nights
    discount = (0.10 * base_price) if early_checkout else 0
    return base_price - discount, discount

# --- DAY 1: GET ENDPOINTS ---
@app.get("/")
def home_route():
    return {'message': 'Welcome to Grand Stay Hotel'}

@app.get("/rooms/summary")
def get_rooms_summary():
    # 1. Basic Counts
    total_rooms = len(rooms_db)
    available_rooms = [r for r in rooms_db if r['is_available']]
    available_count = len(available_rooms)
    occupied_count = total_rooms - available_count
    
    # 2. Price Logic (Handling empty lists to prevent errors)
    all_prices = [r['price_per_night'] for r in rooms_db]
    cheapest = min(all_prices) if all_prices else 0
    expensive = max(all_prices) if all_prices else 0
    
    # 3. Breakdown by Type (e.g., {"Single": 2, "Suite": 2...})
    # This logic looks at every room and counts how many match each type
    room_types = [r['type'] for r in rooms_db]
    type_breakdown = {t: room_types.count(t) for t in set(room_types)}
    
    # 4. Return the full JSON object
    return {
        "total_rooms": total_rooms,
        "available_count": available_count,
        "occupied_count": occupied_count,
        "cheapest_room_price": cheapest,
        "most_expensive_room_price": expensive,
        "breakdown_by_type": type_breakdown
    }

@app.get("/rooms")
def list_all_rooms():
    return {"total": len(rooms_db), "rooms": rooms_db}

# --- DAY 6: SEARCH, SORT, & PAGINATION ---
@app.get("/rooms/search")
def search_rooms(keyword: str = Query(..., min_length=1)):
    results = [r for r in rooms_db if keyword.lower() in r['type'].lower() or keyword.lower() in r['room_number']]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"total_found": len(results), "rooms": results}

@app.get("/rooms/sort")
def sort_rooms(sort_by: str = "price_per_night", order: str = "asc"):
    rev = (order == "desc")
    # Using sorted() as per Day 6 requirements
    return sorted(rooms_db, key=lambda x: x.get(sort_by, "price_per_night"), reverse=rev)

@app.get("/rooms/page")
def paginate_rooms(page: int = Query(1, ge=1), limit: int = Query(2, ge=1)):
    start = (page - 1) * limit
    total_items = len(rooms_db)
    # Using the ceiling division formula from Day 6 hint
    total_pages = -(-total_items // limit) 
    return {
        "page": page,
        "total_pages": total_pages,
        "rooms": rooms_db[start : start + limit]
    }

# --- DAY 3 & 6: COMBINED BROWSE ---
@app.get("/rooms/browse")
def browse_rooms(
    keyword: Optional[str] = None, 
    sort_by: str = "price_per_night", 
    order: str = "asc", 
    page: int = 1, 
    limit: int = 3
):
    # Step 1: Filter/Search
    result = rooms_db
    if keyword:
        result = [r for r in result if keyword.lower() in r['type'].lower()]
    # Step 2: Sort
    result = sorted(result, key=lambda x: x[sort_by], reverse=(order=="desc"))
    # Step 3: Paginate
    start = (page - 1) * limit
    return {
        "total_found": len(result),
        "total_pages": -(-len(result) // limit),
        "products": result[start : start + limit]
    }

# --- DAY 3: FILTER WITH QUERY + IS NOT NONE ---
@app.get("/rooms/filter")
def filter_rooms(
    room_type: Optional[str] = Query(None), 
    floor: Optional[int] = Query(None)
):
    filtered = rooms_db
    if room_type is not None:
        filtered = [r for r in filtered if r['type'].lower() == room_type.lower()]
    if floor is not None:
        filtered = [r for r in filtered if r['floor'] == floor]
    return filtered

# --- DAY 1: GET BY ID (Placed after static routes) ---
@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

# --- DAY 4: CRUD OPERATIONS ---
@app.post("/rooms", status_code=201)
def create_room(room: NewRoom):
    if any(r['room_number'] == room.room_number for r in rooms_db):
        raise HTTPException(status_code=400, detail="Room number already exists")
    new_room_data = room.dict()
    new_room_data['id'] = len(rooms_db) + 1
    rooms_db.append(new_room_data)
    return new_room_data

@app.put("/rooms/{room_id}")
def update_room(room_id: int, price: Optional[int] = None):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if price is not None:
        room['price_per_night'] = price
    return room

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room['is_available']:
        raise HTTPException(status_code=400, detail="Cannot delete an occupied room")
    rooms_db.remove(room)
    return {"message": "Room deleted successfully"}

# --- DATABASE SETUP ---
bookings = []
booking_counter = 1

# --- Q4: GET /bookings (Day 1) ---
@app.get("/bookings")
def get_all_bookings():
    """
    Returns the list of all bookings made so far.
    The 'total' count is placed at the bottom for easy reading.
    """
    return {
        "bookings": bookings,
        "total": len(bookings)
    }

@app.get("/bookings/search")
def search_bookings(guest_name: str):
    results = [b for b in bookings if guest_name.lower() in b['guest_name'].lower()]
    return {"total": len(results), "results": results}

# --- DAY 5: MULTI-STEP WORKFLOW (Booking -> Check-in -> Check-out) ---
@app.post("/bookings", status_code=201)
def create_booking(req: BookingRequest):
    global booking_counter
    room = find_room(req.room_id)
    if not room or not room['is_available']:
        raise HTTPException(status_code=400, detail="Room unavailable or not found")
    
    cost, discount = calculate_stay_cost(room['price_per_night'], req.nights, req.meal_plan, req.early_checkout)
    
    new_booking = {
        "booking_id": booking_counter,
        "guest_name": req.guest_name,
        "total_cost": cost,
        "status": "confirmed"
    }
    room['is_available'] = False
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

@app.post("/bookings/{booking_id}/checkin")
def checkin_guest(booking_id: int):
    for b in bookings:
        if b['booking_id'] == booking_id:
            b['status'] = "checked_in"
            return b
    raise HTTPException(status_code=404, detail="Booking not found")

@app.post("/bookings/{booking_id}/checkout")
def checkout_guest(booking_id: int):
    for b in bookings:
        if b['booking_id'] == booking_id:
            b['status'] = "completed"
            # Find associated room logic would go here to set is_available=True
            return {"message": "Guest checked out", "status": "completed"}
    raise HTTPException(status_code=404, detail="Booking not found")
