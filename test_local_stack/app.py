from flask import Flask, request
import logging

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def home():
    user = request.args.get('user', 'anonymous')
    logging.info(f"User {user} accessed /")
    return f"Hello {user}!"

@app.route('/dashboard')
def dashboard():
    user = request.args.get('user', 'anonymous')
    logging.info(f"User {user} accessed /dashboard")
    return f"Dashboard for {user}"

@app.route('/data')
def data():
    logging.info("Fetching some real data...")
    try:
        # Example error
        result = 10 / int(request.args.get('value', '0'))  # will raise if 0
        logging.info(f"Data processed successfully: {result}")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
    return "Done"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)