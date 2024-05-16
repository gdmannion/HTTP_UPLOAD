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
        
        # Extract 'Content-Disposition' header to get the filename
        content_disposition = self.headers.get('Content-Disposition')
        if content_disposition:
            _, params = cgi.parse_header(content_disposition)
            filename = params.get('filename', 'output_file')
        else:
            filename = f'video_{int(time.time())}.mp4'
        
        full_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(full_path, 'wb') as output_file:
            while True:
                chunk_size = self._read_chunk_size()
                if chunk_size == 0:
                    break
                data = self._read_chunk(chunk_size)
                output_file.write(data)

        self._send_response(f"Video saved as {filename}")

    def _read_chunk_size(self):
        size_str = self.rfile.readline().strip()
        return int(size_str, 16)

    def _read_chunk(self, size):
        data = self.rfile.read(size)
        self.rfile.read(2)  # Read and discard the trailing \r\n characters
        return data

server_address = ('0.0.0.0', 5000)

def run_http_server():
    httpd = HTTPServer(server_address, VideoUploadHandler)
    print('HTTP server listening on port 5000...')
    httpd.serve_forever()

app = Flask(__name__)

@app.route('/')
def display_videos():
    video_info_list = []
    for f in os.listdir(UPLOAD_DIR):
        if f.endswith(('.mp4', '.mkv')):
            file_path = os.path.join(UPLOAD_DIR, f)
            upload_time = os.path.getmtime(file_path)
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upload_time))
            video_info_list.append({'filename': f, 'upload_time': formatted_time})
    return render_template('display001.html', video_info_list=video_info_list)

@app.route('/receive_notification', methods=['GET', 'POST'])
def receive_notification():
    try:
        data = request.json
        print("Received JSON data:", data)
        return jsonify({"message": "Notification received successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    t1 = threading.Thread(target=run_http_server)
    t1.start()
    
    app.run(host='0.0.0.0', port=5001)
