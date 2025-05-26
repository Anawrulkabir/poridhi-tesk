from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
import os
import psycopg2 # For PostgreSQL
import psycopg2.extras # To get results as dictionaries
import json # To handle the task_updates list of objects
from dotenv import load_dotenv # Import load_dotenv

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
CORS(app) # Enable CORS for all routes and origins by default

# DATABASE_URL should be set as an environment variable in your hosting environment (e.g., Vercel)
# Example: postgresql://user:password@host:port/database
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Establishes a connection to the database."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        # In a real app, you might want to handle this more gracefully
        # or ensure the app doesn't start if DB connection fails.
        raise

def init_db():
    """Initializes the database by creating the tasks table if it doesn't exist."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                task_name VARCHAR(255) NOT NULL,
                task_updates JSONB,
                repo_link VARCHAR(512),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        print("Database initialized (tasks table checked/created).")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

# Call init_db() when the app starts to ensure the table exists.
# For Vercel, this might run during the build/deployment phase or on first request.
# It's generally better to handle schema migrations separately in production.
init_db()


@app.route('/add_task', methods=['POST'])
def add_task():
    conn = None
    try:
        data = request.get_json()
        if not data or \
           'name' not in data or \
           'task_name' not in data or \
           'task_updates' not in data or \
           not isinstance(data['task_updates'], list) or \
           not all(isinstance(upd, dict) and 'text' in upd and 'link' in upd for upd in data['task_updates']) or \
           'repo_link' not in data:
            return jsonify({
                "error": "Missing or invalid fields. Required: name (str), task_name (str), task_updates (list of {'text': str, 'link': str}), repo_link (str)"
            }), 400

        name = data['name']
        task_name = data['task_name']
        # Convert task_updates list of dicts to a JSON string for storing in JSONB
        task_updates_json = json.dumps(data['task_updates'])
        repo_link = data['repo_link']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (name, task_name, task_updates, repo_link) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, task_name, task_updates_json, repo_link)
        )
        new_task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        return jsonify({
            "message": "Task added successfully to database", 
            "task_id": new_task_id,
            "task": data # Return the input data for confirmation
        }), 201

    except psycopg2.Error as e:
        # Handle PostgreSQL specific errors
        print(f"Database error: {e}")
        return jsonify({"error": "A database error occurred.", "details": str(e)}), 500
    except ValueError as e: # For DATABASE_URL not set
        print(f"Configuration error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected server error occurred.", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    conn = None
    try:
        conn = get_db_connection()
        # Use RealDictCursor to get results as dictionaries
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT name, task_name, task_updates, repo_link FROM tasks ORDER BY created_at DESC")
        tasks = cur.fetchall()
        cur.close()
        # The task_updates field is already a list of dicts when fetched from JSONB
        return jsonify(tasks), 200
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "A database error occurred while fetching tasks.", "details": str(e)}), 500
    except ValueError as e: # For DATABASE_URL not set
        print(f"Configuration error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected server error occurred while fetching tasks.", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Remove the if __name__ == '__main__': block for Vercel deployment
# Vercel will use a WSGI server like Gunicorn to run the 'app' object.

# if __name__ == '__main__':
#     # init_db() is called at the top level when the script is imported/run.
#     # load_dotenv() is also called at the top level.
#     print("Attempting to run Flask development server...")
#     # You can add a check here to see if DATABASE_URL is loaded
#     db_url = os.environ.get('DATABASE_URL')
#     if db_url:
#         print(f"DATABASE_URL loaded, starts with: {db_url[:30]}...")
#     else:
#         print("DATABASE_URL is NOT loaded. Check your .env file and dotenv setup.")
#     app.run(debug=True, port=5001) # Using port 5001 to avoid common conflicts
