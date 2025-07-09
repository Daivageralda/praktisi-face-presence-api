import uvicorn as uc

try:
    if __name__ == "__main__":
        uc.run(
            'src.app:app',  # Mengarah ke apps/app.py -> app
            host="localhost",
            port=8888,
            reload=True
        )
except Exception as e:
    print(f'Error: {e}')
