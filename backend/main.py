from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import torch
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image
import json
import io
from datetime import datetime
import sqlite3
import os 

from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "disease_model.pth")
CLASSES_PATH = os.path.join(BASE_DIR, "..", "models", "class_names.json") 

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-flash-lite-latest") 

with open(CLASSES_PATH) as f:
    class_names = json.load(f)

model = models.efficientnet_b0(weights=None)
model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_names))
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

TREATMENT_INFO = {
    "Pepper__bell___Bacterial_spot": "Apply copper-based bactericide. Avoid overhead watering and handling wet plants. Remove and destroy infected plant debris.",
    "Pepper__bell___healthy": "No disease detected. Your pepper plant looks healthy!",
    "Potato___Early_blight": "Apply fungicide containing chlorothalonil or mancozeb. Remove infected lower leaves and ensure proper plant spacing for airflow.",
    "Potato___Late_blight": "Apply copper-based fungicide immediately, this spreads fast. Destroy severely infected plants to prevent field-wide spread.",
    "Potato___healthy": "No disease detected. Your potato plant looks healthy!",
    "Tomato_Bacterial_spot": "Apply copper-based bactericide. Avoid working with plants when wet, and rotate crops next season.",
    "Tomato_Early_blight": "Remove affected lower leaves, apply fungicide with chlorothalonil, and mulch to prevent soil splash onto leaves.",
    "Tomato_Late_blight": "Apply copper-based fungicide immediately. Remove and destroy infected plants, this disease spreads very quickly in humid conditions.",
    "Tomato_Leaf_Mold": "Improve greenhouse or field ventilation, reduce humidity, and apply a fungicide labeled for leaf mold.",
    "Tomato_Septoria_leaf_spot": "Remove infected leaves promptly, apply fungicide with chlorothalonil, and avoid overhead watering.",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Spray with insecticidal soap or neem oil. Increase humidity, as mites thrive in dry conditions.",
    "Tomato__Target_Spot": "Apply fungicide with chlorothalonil or mancozeb. Remove infected leaves and improve air circulation.",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "No cure once infected. Remove and destroy infected plants. Control whiteflies, which spread this virus.",
    "Tomato__Tomato_mosaic_virus": "No cure once infected. Remove and destroy infected plants. Disinfect tools between uses.",
    "Tomato_healthy": "No disease detected. Your tomato plant looks healthy!"
}

DB_PATH = os.path.join(BASE_DIR, "detections.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_class TEXT,
    confidence REAL,
    lat REAL,
    lon REAL,
    timestamp TEXT
)
""")
conn.commit()


@app.get("/")
def root():
    return {"message": "Smart Farming Assistant API is running"}


@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...), lat: float = 0.0, lon: float = 0.0):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    input_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, 1)

    disease = class_names[predicted.item()]
    conf_score = float(confidence.item())

    conn.execute(
        "INSERT INTO detections (disease_class, confidence, lat, lon, timestamp) VALUES (?, ?, ?, ?, ?)",
        (disease, conf_score, lat, lon, datetime.now().isoformat())
    )
    conn.commit()

    treatment = TREATMENT_INFO.get(disease, "No treatment info available yet for this class.")

    return {
        "disease": disease,
        "confidence": round(conf_score, 3),
        "treatment": treatment
    }


@app.get("/regional-stats")
def regional_stats():
    rows = conn.execute("SELECT disease_class, lat, lon, timestamp FROM detections").fetchall()
    return [{"disease": r[0], "lat": r[1], "lon": r[2], "timestamp": r[3]} for r in rows] 

@app.post("/chat")
async def chat(disease: str, question: str):
    prompt = f"""You are an agricultural expert helping a farmer.
Disease detected: {disease}
Farmer's question: {question}
Give a short, simple, practical answer (2-4 sentences) in plain language a farmer without technical background can understand."""

    response = gemini_model.generate_content(prompt)
    return {"answer": response.text} 

