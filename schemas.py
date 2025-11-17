"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Course marketplace schemas

class Course(BaseModel):
    """
    Courses collection schema
    Collection name: "course"
    """
    title: str = Field(..., description="Course title")
    slug: str = Field(..., description="URL-friendly identifier")
    description: str = Field(..., description="Short description")
    category: str = Field(..., description="Primary category")
    level: str = Field("Beginner", description="Beginner, Intermediate, Advanced")
    instructor_name: str = Field(..., description="Instructor display name")
    thumbnail: str = Field(..., description="Image URL")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating 0-5")
    rating_count: int = Field(0, ge=0, description="Number of ratings")
    students: int = Field(0, ge=0, description="Number of enrolled students")
    lessons: int = Field(0, ge=0, description="Lesson count")
    language: str = Field("English", description="Course language")
    duration: str = Field("8h 30m", description="Human-friendly duration")
    is_free: bool = Field(False, description="Whether the course is free")
    price: float = Field(0, ge=0, description="Current price")
    old_price: Optional[float] = Field(None, ge=0, description="Original price if discounted")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
