# Zero-Cloud Council Prioritization Engine

This is the backend for the "Zero-Cloud Council Prioritization Engine" developed during the NVIDIA hackathon. 

The system ingests citizen reports (images) of city issues, uses a local Vision-Language Model (VLM) via Nemotron 3 Super to extract data, enriches it with local static CSV data (population density) and live API data (TfL traffic disruptions), and calculates a deterministic priority score. All AI inference runs locally without cloud APIs.

## Project Structure
- `/data/`: Contains static datasets (e.g., `density.csv`).
- `/routers/`: FastAPI endpoint definitions.
- `/services/`: Business logic for API integrations, Datastore lookup, Scoring, and local VLM execution.
- `main.py`: Application entry point.
- `requirements.txt`: Python dependencies.

---

## 🛠️ Environment Setup (CRITICAL)

Since we are a team of 4 sharing a DGX Spark and running heavy models like **Nemotron 3 Super**, it is **critical** to use a virtual environment. This prevents system-level package conflicts and ensures everyone is running the exact same dependency versions for PyTorch, Transformers, FastAPI, etc.

You can set up your isolated environment using either standard `venv` or `conda` (recommended for DGX).

### Option 1: Conda (Recommended for DGX)
Conda handles complex CUDA dependencies much better than standard pip.

```bash
# 1. Create a fresh conda environment
conda create -n seeit-sortit python=3.10

# 2. Activate the environment
conda activate seeit-sortit

# 3. Install requirements
pip install -r requirements.txt
```

### Option 2: Standard Python venv
If you prefer standard python environments:

```bash
# 1. Create the virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt
```

---

## 🚀 Running the API

Once your virtual environment is active and dependencies are installed, you can start the local development server:

```bash
uvicorn main:app --reload
```

- The API will be available at `http://localhost:8000`
- You can access the interactive Swagger documentation and test the `/submit-report` endpoint by visiting `http://localhost:8000/docs`.

## 🧪 Testing the Endpoint
You can test the `POST /submit-report` endpoint using the FastAPI interactive docs or `curl`:

```bash
curl -X 'POST' \
  'http://localhost:8000/submit-report' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@/path/to/test_image.jpg'
```
