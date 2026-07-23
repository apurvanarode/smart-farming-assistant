# System Design: Smart Farming Assistant

This document outlines architectural decisions, current limitations, and the production roadmap for the Smart Farming Assistant. It reflects an honest assessment of what was built in a 4-day scoped MVP versus what a production-grade deployment would require.

---

## 1. Current Architecture (as built)
[Farmer's browser]
|
v
[Streamlit frontend] --- calls ---> [FastAPI backend]
|
|--> [PyTorch CV model] (disease classification)
|--> [Gemini API] (treatment chatbot)
|--> [SQLite] (detection logs)
|
v
[Streamlit dashboard] (regional stats)
The system is a monolithic FastAPI service serving three responsibilities: image inference, conversational Q&A, and detection logging. This is appropriate for the current scale (single-user demo) but would need to be decomposed for real multi-region deployment (see Section 4).

---

## 2. Why SQLite, and when to move to PostgreSQL + PostGIS

SQLite was chosen for the 4-day build because it requires no separate server process, no connection configuration, and ships as a single file — ideal for rapid local development and demoing.

**Limitations of this choice at scale:**
- SQLite handles concurrent writes poorly; multiple farmers submitting detections simultaneously would cause write locks
- No native geospatial query support (e.g., "find all detections within 10km of point X" requires manual lat/lon math instead of proper spatial indexing)

**Production plan:** migrate to PostgreSQL with the PostGIS extension. This would allow:
- Proper concurrent write handling via connection pooling
- Native geospatial queries (`ST_DWithin`, spatial indexes) for efficient "nearby outbreak" lookups at regional scale
- Straightforward horizontal read scaling via read replicas as detection volume grows

---

## 3. Offline-First Design (not yet implemented, designed here)

Rural farmers frequently have unreliable or no internet connectivity. The current MVP requires a live connection to both the FastAPI backend and the Gemini API — a real deployment blocker for the target user.

**Proposed architecture for offline support:**

1. **Client-side model inference:** Export the trained PyTorch model to ONNX or TensorFlow Lite format. This allows the disease classification step to run directly on a farmer's phone/browser without a network call, even completely offline. Given the model is a fine-tuned EfficientNet-B0 (relatively lightweight), on-device inference is feasible with acceptable latency on modern mid-range phones.

2. **Local request queue:** When offline, diagnosis requests (image + metadata) get stored in the browser's IndexedDB (for a web app) or local device storage (for a native/PWA app), rather than failing outright.

3. **Background sync:** Using a Service Worker (for a Progressive Web App architecture), queued requests automatically sync to the backend once connectivity returns — updating the regional detection log and allowing the chatbot follow-up (which does require a live connection) to become available.

4. **Graceful degradation for the chatbot specifically:** Since the Gemini API call cannot run on-device, the treatment info dictionary (`TREATMENT_INFO` in the current backend) already provides baseline offline guidance without needing a live LLM call. The chatbot becomes an "enhanced" experience layered on top of always-available static guidance, not a hard dependency.

**Tradeoff being made:** on-device inference sacrifices some accuracy/model size flexibility (we'd likely need to distill or quantize the model further) in exchange for reliability in low-connectivity conditions, which is the actual constraint most relevant users face.

---

## 4. Scaling the Backend (multi-region, multi-user)

The current single FastAPI process would need to be decomposed as usage grows:

- **Inference service:** separated out behind a queue (e.g., a lightweight task queue) so image classification doesn't block the request thread — important once concurrent users exceed what a single process can handle synchronously
- **Chat service:** rate-limited and cached separately from inference, since LLM API calls are the slowest and most expensive part of any single request
- **Detection-logging service:** writes to PostgreSQL/PostGIS, decoupled from the above two so a spike in diagnosis requests doesn't affect dashboard read performance for agri-department users viewing regional stats

---

## 5. Known Limitations of the Current Model (honest assessment)

- **Trained on PlantVillage**, a dataset of lab-condition images (uniform backgrounds, controlled lighting). Real farmer-submitted photos will be noisier — variable lighting, cluttered backgrounds, partial leaf visibility — and accuracy will likely be meaningfully lower in the field than the ~98% training accuracy achieved here.
- **Scoped to 15 classes** across three crops (Pepper, Potato, Tomato) due to the dataset variant used and the 4-day build window, not the full 38-class PlantVillage set.
- **No automated retraining pipeline yet.** The current model is a single static snapshot. A production system would need a feedback loop: farmers confirming/correcting diagnoses, that feedback accumulating, and periodic retraining triggered once enough new labeled data exists — likely orchestrated via a scheduled job (e.g., GitHub Actions or a proper MLOps pipeline like MLflow + Airflow) rather than the manual Colab-based training used here.
- **Chatbot model selection was constrained by free-tier API quota availability** during development (see main README for details), not by a technical architecture decision — this is trivially swappable for a paid-tier model once budget allows.

---

## 6. Summary of Next Steps (in priority order for a real deployment)

1. Migrate SQLite → PostgreSQL + PostGIS
2. Build feedback collection (farmer confirms/corrects diagnosis) and a retraining trigger
3. Export model to ONNX/TFLite for on-device inference
4. Implement offline queue + background sync (PWA architecture)
5. Expand dataset beyond lab-condition images (incorporate real field photos, e.g., via PlantDoc or crowd-sourced farmer submissions with consent)
6. Decompose backend into separate inference/chat/logging services as usage grows