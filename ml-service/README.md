Testing locally: 
- uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
- curl -X GET http://localhost:8000/predict-entire