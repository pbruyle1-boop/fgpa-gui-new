#!/usr/bin/env python3
"""
Simple HTTP server for hosting FPGA Controller web interface
Serves files from the current directory on port 8080
"""

import http.server
import socketserver
import os
import socket

def get_ip_address():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"

def main():
    PORT = 8080
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Check if HTML file exists in parent directory
    html_file = os.path.join(parent_dir, "fpga_controller.html")
    if os.path.exists(html_file):
        os.chdir(parent_dir)
    else:
        # Try current directory
        html_file = "fpga_controller.html"
        if not os.path.exists(html_file):
            print("Error: fpga_controller.html not found!")
            print("Please run this script from the fpga_controller directory")
            return 1
    
    ip_address = get_ip_address()
    
    # Custom handler to add CORS headers if needed
    class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    Handler = CORSHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"FPGA Controller Web Server")
            print(f"Serving at: http://{ip_address}:{PORT}")
            print(f"Local access: http://localhost:{PORT}")
            print(f"Web interface: http://{ip_address}:{PORT}/fpga_controller.html")
            print("")
            print("Press Ctrl+C to stop the server")
            print("")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        return 0
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Error: Port {PORT} is already in use!")
            print("Try stopping any existing web servers or use a different port")
            return 1
        else:
            print(f"Error starting server: {e}")
            return 1

if __name__ == "__main__":
    exit(main())
