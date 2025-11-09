"""
FastAPI REST API with CRUD Operations
A complete REST API example with proper error handling and validation
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Product Management API",
    description="A REST API for managing products with full CRUD operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    description: Optional[str] = Field(None, max_length=500, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be greater than 0)")
    quantity: int = Field(..., ge=0, description="Product quantity in stock")
    category: str = Field(..., min_length=1, max_length=50, description="Product category")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "quantity": 50,
                "category": "Electronics",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }

# In-memory database (replace with actual database in production)
products_db = {}
next_id = 1

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("🚀 FastAPI application starting up...")
    print("📝 API documentation available at: http://localhost:8000/docs")
    # Add some sample data
    global next_id
    sample_products = [
        {
            "name": "Laptop",
            "description": "High-performance laptop for professionals",
            "price": 999.99,
            "quantity": 50,
            "category": "Electronics"
        },
        {
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse",
            "price": 29.99,
            "quantity": 200,
            "category": "Accessories"
        }
    ]
    for product_data in sample_products:
        now = datetime.now()
        products_db[next_id] = {
            "id": next_id,
            **product_data,
            "created_at": now,
            "updated_at": now
        }
        next_id += 1

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "total_products": len(products_db)
    }

# CRUD Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to Product Management API",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/products", response_model=List[Product], tags=["Products"])
async def get_all_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None
):
    """
    Retrieve all products with optional filtering and pagination
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    - **category**: Filter by category (optional)
    """
    products = list(products_db.values())
    
    # Filter by category if provided
    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    
    # Apply pagination
    return products[skip: skip + limit]

@app.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product(product_id: int):
    """
    Retrieve a specific product by ID
    
    - **product_id**: The ID of the product to retrieve
    """
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return products_db[product_id]

@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED, tags=["Products"])
async def create_product(product: ProductCreate):
    """
    Create a new product
    
    - **name**: Product name (required)
    - **description**: Product description (optional)
    - **price**: Product price (required, must be > 0)
    - **quantity**: Product quantity (required, must be >= 0)
    - **category**: Product category (required)
    """
    global next_id
    now = datetime.now()
    
    new_product = {
        "id": next_id,
        **product.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    
    products_db[next_id] = new_product
    next_id += 1
    
    return new_product

@app.put("/products/{product_id}", response_model=Product, tags=["Products"])
async def update_product(product_id: int, product_update: ProductUpdate):
    """
    Update an existing product
    
    - **product_id**: The ID of the product to update
    - All fields are optional; only provided fields will be updated
    """
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    stored_product = products_db[product_id]
    update_data = product_update.model_dump(exclude_unset=True)
    
    # Update only provided fields
    for field, value in update_data.items():
        stored_product[field] = value
    
    stored_product["updated_at"] = datetime.now()
    
    return stored_product

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
async def delete_product(product_id: int):
    """
    Delete a product
    
    - **product_id**: The ID of the product to delete
    """
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    del products_db[product_id]
    return None

@app.get("/products/category/{category}", response_model=List[Product], tags=["Products"])
async def get_products_by_category(category: str):
    """
    Retrieve all products in a specific category
    
    - **category**: The category to filter by
    """
    products = [p for p in products_db.values() if p["category"].lower() == category.lower()]
    
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No products found in category '{category}'"
        )
    
    return products

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "fastapi_rest_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
