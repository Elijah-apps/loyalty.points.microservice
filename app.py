from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

# Model for a user
class User(BaseModel):
    id: int
    username: str

# Model to track points transactions
class PointsTransaction(BaseModel):
    user_id: int
    points: int
    transaction_type: str  # E.g., 'earn', 'redeem'
    transaction_date: datetime

# Loyalty points model
class LoyaltyPoints(BaseModel):
    user_id: int
    points_balance: int

# Simulating databases
users_db = []
loyalty_points_db = []
points_transactions_db = []

# Route to register a user
@app.post("/api/register-user")
def register_user(user: User):
    if any(u.id == user.id for u in users_db):
        raise HTTPException(status_code=400, detail="User already exists")
    
    users_db.append(user)
    loyalty_points_db.append(LoyaltyPoints(user_id=user.id, points_balance=0))  # Initialize points to 0
    return {"message": f"User {user.username} registered successfully!"}

# Route to get all users
@app.get("/api/users", response_model=List[User])
def get_users():
    if not users_db:
        raise HTTPException(status_code=404, detail="No users found")
    return users_db

# Route to earn points (for an action)
@app.post("/api/earn-points")
def earn_points(user_id: int, points: int):
    # Check if the user exists
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find user's loyalty points and update balance
    loyalty_points = next((lp for lp in loyalty_points_db if lp.user_id == user_id), None)
    if not loyalty_points:
        raise HTTPException(status_code=404, detail="Loyalty points record not found")
    
    # Update points balance
    loyalty_points.points_balance += points
    
    # Log the points transaction
    transaction = PointsTransaction(
        user_id=user_id,
        points=points,
        transaction_type="earn",
        transaction_date=datetime.now()
    )
    points_transactions_db.append(transaction)

    return {"message": f"{points} points earned for {user.username}!", "new_balance": loyalty_points.points_balance}

# Route to redeem points (for a reward)
@app.post("/api/redeem-points")
def redeem_points(user_id: int, points: int):
    # Check if the user exists
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find user's loyalty points
    loyalty_points = next((lp for lp in loyalty_points_db if lp.user_id == user_id), None)
    if not loyalty_points:
        raise HTTPException(status_code=404, detail="Loyalty points record not found")
    
    # Check if the user has enough points
    if loyalty_points.points_balance < points:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    # Redeem points
    loyalty_points.points_balance -= points
    
    # Log the points transaction
    transaction = PointsTransaction(
        user_id=user_id,
        points=-points,
        transaction_type="redeem",
        transaction_date=datetime.now()
    )
    points_transactions_db.append(transaction)

    return {"message": f"{points} points redeemed by {user.username}!", "new_balance": loyalty_points.points_balance}

# Route to check points balance for a user
@app.get("/api/points-balance/{user_id}")
def get_points_balance(user_id: int):
    # Check if the user exists
    loyalty_points = next((lp for lp in loyalty_points_db if lp.user_id == user_id), None)
    if not loyalty_points:
        raise HTTPException(status_code=404, detail="Loyalty points record not found")
    
    return {"user_id": user_id, "points_balance": loyalty_points.points_balance}

# Route to get points transaction history for a user
@app.get("/api/points-transactions/{user_id}", response_model=List[PointsTransaction])
def get_points_transactions(user_id: int):
    # Get all transactions for the user
    user_transactions = [t for t in points_transactions_db if t.user_id == user_id]
    if not user_transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    
    return user_transactions

# Route to get the total points earned by a user
@app.get("/api/total-earned-points/{user_id}")
def get_total_earned_points(user_id: int):
    # Get all earned points transactions for the user
    earned_transactions = [t for t in points_transactions_db if t.user_id == user_id and t.transaction_type == "earn"]
    
    total_earned = sum(t.points for t in earned_transactions)
    return {"user_id": user_id, "total_earned_points": total_earned}

# Root route with a welcome message
@app.get("/")
def read_root():
    return {"message": "Welcome to the Loyalty Points Microservice!"}

# Run the app using uvicorn (this can be done directly or using the command line)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
