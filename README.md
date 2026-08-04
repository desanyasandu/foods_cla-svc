# foods-cla-svc

AI Food Recognition API using FastAPI, MongoDB, and Ultralytics YOLO.

Detect foods from images, retrieve nutrition data, and manage meal tracking through a RESTful API.

## Features

- **Food Detection** — Upload an image and get identified food items with confidence scores using YOLOv8
- **Nutrition Lookup** — Automatic nutrition data retrieval for detected foods from MongoDB
- **Detection History** — Store and retrieve past detection records with predictions and bounding boxes
- **Meal Management** — Create and track meals with associated foods and nutritional totals
- **CRUD Operations** — Full create/read/update/delete for foods, nutrition entries, and meals

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| Database | MongoDB (Motor async driver) |
| ML Model | Ultralytics YOLOv8 (`best.pt`) |
| Validation | Pydantic v2 |
| Server | Uvicorn |

## Project Structure

```
foods-cla-svc/
├── main.py                  # FastAPI app entry point with lifespan management
├── db.py                    # Async MongoDB connection (Motor)
├── models.py                # Pydantic models (Food, Nutrition, Meal, Detection, etc.)
├── routes/
│   ├── detect.py            # POST /detect/ — image-based food detection
│   ├── detection.py         # CRUD for detection history records
│   ├── food.py              # CRUD for food items
│   ├── nutrition.py         # CRUD for nutrition data
│   └── meal.py              # CRUD for meals
├── services/
│   ├── yolo_service.py      # YOLO model loading, detection, and mock fallback
│   └── best.pt              # YOLOv8 food detection model
└── README.md
```

## API Endpoints

### Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/detect/` | Upload an image and detect foods with nutrition data |

**Request:** `multipart/form-data` with field `image` (file)

**Response:**
```json
{
  "foods": [
    {
      "name": "Banana",
      "confidence": 0.95,
      "calories": 89,
      "protein": 1.1,
      "fat": 0.3,
      "carbohydrates": 23,
      "fiber": 2.6,
      "category": "Fruit",
      "image_url": "https://example.com/banana.jpg"
    }
  ]
}
```

### Detections (History)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/detections/` | List all detection records |
| `GET` | `/detections/{id}` | Get a specific detection by ID |
| `DELETE` | `/detections/{id}` | Delete a detection record |
| `POST` | `/detections/` | Upload image, detect foods, and store the record |

### Foods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/foods/` | List all foods |
| `POST` | `/foods/` | Create a new food item |

### Nutrition

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/nutrition/` | List all nutrition entries |
| `GET` | `/nutrition/{food_id}` | Get nutrition for a specific food |
| `POST` | `/nutrition/` | Create a nutrition entry |

### Meals

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/meals/` | List all meals |
| `POST` | `/meals/` | Create a meal with associated foods |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |

## Setup & Installation

### Prerequisites

- Python 3.12+
- MongoDB (running locally or accessible via `MONGODB_URL`)
- UV package manager

### Install dependencies

```bash
uv sync
```

This installs all runtime dependencies plus CPU-only PyTorch (for YOLO).

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MODEL_PATH` | `best.pt` | Path to the YOLO model file |

### Run the development server

```bash
uv run fastapi dev main.py
```

The server starts at `http://127.0.0.1:8000` with auto-reload enabled.

- API docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## How It Works

1. **Image Upload** — A client uploads an image via `POST /detect/` as `multipart/form-data`
2. **Validation** — The file extension and size are validated (max 50MB, allowed: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`)
3. **YOLO Detection** — The image is passed to the YOLOv8 model (`best.pt`) for food item detection
4. **Fallback** — If the model fails to load or detects nothing, mock detection returns sample food items
5. **Nutrition Lookup** — Each detected food name is looked up in the MongoDB `foods` and `nutrition` collections
6. **Response** — A `DetectionResponse` is returned with food names, confidence scores, and nutrition data

## Model

The YOLOv8 model (`services/best.pt`) is trained on a custom food dataset with 38 classes including:

`Banana`, `Corn`, `Rice`, `Roti`, `Salad`, `Chicken`, `Fish`, `Egg`, `Cheese Pizza`, `Fried Rice`, `Biriyani`, `Chocolate`, `Ice Cream`, `Tea`, `Noodles`, `Potato`, `Papaw`, `Mango`, `Avocado`, `Pizza`, `Sauces`, `Sticks`, `Sausages`, `Curry`, `Kottu`, `White Chocolate`, `Chocolate Milkshake`, `Lemon Juice`, `Hot Dog`, `Sandwich`

## License

MIT
