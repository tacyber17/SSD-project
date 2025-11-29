"""
Development server runner.
Run this file directly to start the Flask development server without Docker.

Usage:
    python run.py

Or use Flask CLI:
    flask run

The application will be available at http://localhost:5000
"""
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    print("Starting Flask development server...")
    print("Application will be available at http://localhost:5000")
    print("Press CTRL+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)


