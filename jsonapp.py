import os
import logging
import threading
import cgi
from http.server import BaseHTTPRequestHandler, HTTPServer
from flask import Flask, render_template, request, jsonify
import time

# Set up logging with a DEBUG level
logging.basicConfig(level=logging.DEBUG)

# Define the directory where videos will be uploaded
UPLOAD_DIR = 'static/uploads'
# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Define a custom HTTP request handler for video uploads
class VideoUploadHandler(BaseHTTPRequestHandler):

    # Helper function to send an HTTP response
    def _send_response(self, message):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(message.encode())

    # Handle GET requests
    def do_GET(self):
        self._send_response(f"GET request for {self.path}")

    # Handle POST requests
    def do_POST(self):
        logging.info(f"POST request,\nPath: {self.path}\nHeaders:\n{self.headers}\n")
        
        # Print headers for debugging
        print(self.headers)
        
        # Extract 'Content-Disposition' header to get the filename
        content_disposition = self.headers.get('Content-Disposition')
        if content_disposition:
            _, params = cgi.parse_header(content_disposition)
            filename = params.get('filename', 'output_file')
        else:
            # Use a default filename based on the current time if no filename is provided
            filename = f'video_{int(time.time())}.mp4'
        
        # Construct the full path to save the video
        full_path = os.path.join(UPLOAD_DIR, filename)
        
        # Open the file and write the request body data into it
        with open(full_path, 'wb') as output_file:
            while True:
                chunk_size = self._read_chunk_size()
                if chunk_size == 0:
                    break
                data = self._read_chunk(chunk_size)
                output_file.write(data)

        # Respond with a message indicating the video has been saved
        self._send_response(f"POST request for {self.path} received and saved as {filename}")

    # Helper function to read the size of the next chunk of data
    def _read_chunk_size(self):
        size_str = self.rfile.readline().strip()
        return int(size_str, 16)

    # Helper function to read a chunk of data of the given size
    def _read_chunk(self, size):
        data = self.rfile.read(size)
        self.rfile.read(2)  # Read and discard the trailing \r\n characters
        return data

# Define the address and port for the HTTP server
server_address = ('0.0.0.0', 5000)

# Function to start the HTTP server
def run_http_server():
    httpd = HTTPServer(server_address, VideoUploadHandler)
    print('HTTP server listening on port 5000...')
    httpd.serve_forever()

# Initialize Flask application
app = Flask(__name__)

# Flask route to display videos
@app.route('/')
def display_videos():
    video_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.mp4', '.mkv'))]
    print("Detected video files:", video_files)
    return render_template('display.html', video_files=video_files)

# Flask route to receive notifications
@app.route('/receive_notification', methods=['GET','POST'])
def receive_notification():
    try:
        data = request.json  # Parse JSON data from the request
        # Handle the received JSON data here (e.g., log it)
        print("Received JSON data:", data)
        return jsonify({"message": "Notification received successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
# Main execution point
if __name__ == '__main__':
    # Start the HTTP server in a separate thread
    t1 = threading.Thread(target=run_http_server)
    t1.start()

    # Start the Flask app in the main thread
    app.run(host='0.0.0.0', port=5001)