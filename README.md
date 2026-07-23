# 🌱 Smart Farming Assistant

An AI-powered crop disease detection and advisory system built for small farmers with limited access to agronomists. Upload a photo of a crop leaf, get an instant diagnosis, ask follow-up questions to an AI chatbot, and see regional disease outbreak trends on a live dashboard.

## The Problem

Small farmers often lose 20-40% of crop yield to diseases that go undetected until visible damage has already spread — largely due to limited access to agronomists, especially in rural areas. By the time symptoms are obvious to the naked eye, treatment options are often more limited and costly.

## What This Does

1. **Diagnose**: Upload a photo of a crop leaf → a fine-tuned computer vision model identifies the disease (or confirms the plant is healthy) with a confidence score
2. **Get Treatment Advice**: Instantly receive practical treatment guidance
3. **Ask Follow-Up Questions**: A Gemini-powered chatbot answers farmer-specific questions in plain language (e.g., "is this safe to eat if I already harvested it?")
4. **Regional Insights**: Every detection is logged with location data, powering a live dashboard showing disease outbreak patterns — useful for agricultural officers monitoring regional trends

## Demo

*(Add a screen recording or GIF here — see "What I'd Add With More Time" below for how to capture one)*

## Architecture
[Farmer's browser]
|
v
[Streamlit frontend] ---> [FastAPI backend] ---> [PyTorch CV model] (disease classification)
| ---> [Gemini API] (treatment chatbot)
| ---> [SQLite] (detection logging)
v
[Streamlit dashboard] (regional outbreak map + trends)
Full architectural reasoning, scaling plans, and known limitations are documented in [`docs/system_design.md`](docs/system_design.md).

## Tech Stack

| Layer | Technology |
|---|---|
| Computer Vision | PyTorch, EfficientNet-B0 (transfer learning) |
| GenAI Chatbot | Google Gemini API (`gemini-flash-lite-latest`) |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | SQLite (PostgreSQL + PostGIS planned — see system design doc) |
| Data Visualization | Plotly |
| Training Environment | Google Colab (free T4 GPU) |

## Dataset & Model

- Trained on the [PlantVillage dataset](https://www.kaggle.com/datasets/emmarex/plantdisease) — 15 classes across three crops: **Pepper, Potato, and Tomato** (a scoped subset, not the full 38-class dataset, to fit a focused build timeline)
- Model: EfficientNet-B0, fine-tuned via transfer learning, 5 epochs
- **Training accuracy: 98.3%**

**Honest limitation:** PlantVillage images are captured in lab conditions (uniform backgrounds, controlled lighting). Real farmer-submitted field photos are noisier, so real-world accuracy is expected to be meaningfully lower than training accuracy. This gap — and the plan to address it — is discussed in the system design doc.

## How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/apurvanarode/smart-farming-assistant.git
cd smart-farming-assistant
```

### 2. Set up the environment
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Add your own Gemini API key
Create a `.env` file in the project root:
GEMINI_API_KEY=your-key-here
Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### 4. Model files
The trained model files (`disease_model.pth`, `class_names.json`) are included directly in this repo under `models/` — no separate download needed.

### 5. Run the backend
```bash
cd backend
uvicorn main:app --reload
```

### 6. Run the frontend (in a new terminal)
```bash
cd frontend
streamlit run app.py
```

### 7. Run the dashboard (in another new terminal)
```bash
cd frontend
streamlit run dashboard.py --server.port 8502
```

## What I'd Build Next

- Migrate SQLite → PostgreSQL + PostGIS for proper geospatial queries at scale
- On-device model inference (ONNX/TFLite export) for offline-first usage in low-connectivity areas
- Automated retraining pipeline triggered by farmer feedback (active learning loop)
- Expand training data with real field-condition photos, not just lab-condition images
- Decompose the backend into separate inference/chat/logging services as usage scales

See [`docs/system_design.md`](docs/system_design.md) for the full reasoning behind these priorities.

## Project Structure
smart-farming-assistant/
├── backend/ # FastAPI server (diagnosis + chatbot endpoints)
├── frontend/ # Streamlit apps (main app + regional dashboard)
├── models/ # Trained model weights + class labels
├── data/ # Dataset (not committed — see .gitignore)
├── notebooks/ # Training scripts
├── docs/ # System design documentation
└── README.md