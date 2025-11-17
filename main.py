import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db
from schemas import Course

app = FastAPI(title="Courses API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CoursesResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


@app.get("/")
def read_root():
    return {"message": "Courses API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            _ = db.list_collection_names()
            response["connection_status"] = "Connected"
            response["collections"] = _[:10]
            response["database"] = "✅ Connected & Working"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"

    return response


# Utility

def serialize_course(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    return d


@app.get("/api/courses", response_model=CoursesResponse)
def list_courses(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    is_free: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    tag: Optional[str] = Query(None),
    sort: Optional[str] = Query("popular", description="popular|rating|new|price_asc|price_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(9, ge=1, le=60),
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filters: Dict[str, Any] = {}
    if q:
        filters["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"instructor_name": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filters["category"] = category
    if level:
        filters["level"] = level
    if is_free is not None:
        filters["is_free"] = is_free
    if tag:
        filters["tags"] = {"$in": [tag]}
    if min_price is not None or max_price is not None:
        price: Dict[str, Any] = {}
        if min_price is not None:
            price["$gte"] = min_price
        if max_price is not None:
            price["$lte"] = max_price
        filters["price"] = price
    if min_rating is not None:
        filters["rating"] = {"$gte": min_rating}

    sort_map = {
        "popular": ("students", -1),
        "rating": ("rating", -1),
        "new": ("created_at", -1),
        "price_asc": ("price", 1),
        "price_desc": ("price", -1),
    }
    sort_field, sort_dir = sort_map.get(sort, ("students", -1))

    collection = db["course"]
    total = collection.count_documents(filters)
    skip = (page - 1) * page_size

    cursor = (
        collection.find(filters)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(page_size)
    )
    items = [serialize_course(doc) for doc in cursor]

    total_pages = (total + page_size - 1) // page_size if page_size else 1

    return CoursesResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@app.get("/api/courses/filters")
def get_filters():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    collection = db["course"]
    categories = sorted(collection.distinct("category"))
    levels = sorted(collection.distinct("level"))
    tags = sorted(collection.distinct("tags")) if hasattr(collection, 'distinct') else []
    return {"categories": categories, "levels": levels, "tags": tags}


@app.post("/api/courses/seed")
def seed_courses():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    collection = db["course"]
    if collection.count_documents({}) > 0:
        return {"status": "ok", "message": "Courses already seeded"}

    sample: List[Course] = []
    base_tags = [["Design", "UX"], ["Programming", "JavaScript"], ["Marketing"], ["Business"], ["Data"], ["Photography"], ["Health"], ["Music"], ["Finance"], ["AI"], ["Cloud"], ["Product"]]
    categories = ["Design", "Development", "Marketing", "Business", "Data Science", "Photography", "Health & Fitness", "Music", "Finance", "AI", "Cloud", "Product"]
    levels = ["Beginner", "Intermediate", "Advanced"]

    for i in range(1, 25):
        cat = categories[i % len(categories)]
        lvl = levels[i % len(levels)]
        is_free = i % 5 == 0
        price = 0 if is_free else float(9 + (i % 6) * 10)
        old_price = None if is_free or i % 3 != 0 else price + 20
        sample.append(
            Course(
                title=f"Course {i}: Master {cat} {lvl}",
                slug=f"course-{i}",
                description="Learn with hands-on projects, quizzes and expert guidance.",
                category=cat,
                level=lvl,
                instructor_name=f"Instructor {i}",
                thumbnail=f"https://picsum.photos/seed/course{i}/600/400",
                rating=round(3.5 + (i % 15) * 0.1, 1) if not is_free else 4.2,
                rating_count=50 + i * 3,
                students=200 + i * 20,
                lessons=10 + i % 15,
                language="English",
                duration=f"{6 + (i % 8)}h {(i * 7) % 60}m",
                is_free=is_free,
                price=price,
                old_price=old_price,
                tags=base_tags[i % len(base_tags)],
            )
        )

    docs = [c.model_dump() for c in sample]
    for d in docs:
        d["created_at"] = d["updated_at"] = os.getenv("NOW") or None
    collection.insert_many(docs)

    return {"status": "ok", "inserted": len(docs)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
