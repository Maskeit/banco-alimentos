try:
    from app import app
except Exception as e:
    raise SystemExit(f"Error importing Flask app: {e}")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
