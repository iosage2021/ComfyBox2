#!/usr/bin/env python

import http.server
import socketserver
import argparse
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--listen", type=str, default="localhost", help="Listen address for ComfyBox server")
parser.add_argument("-p", "--port", type=int, default=8000, help="Port for ComfyBox server")
args = parser.parse_args()

message = f"""Starting ComfyBox.
Be sure you've started ComfyUI already using this command:

     python main.py --enable-cors-header

Serving at http://{args.listen}:{args.port}...
"""

# python -m http.server will sometimes send incorrect MIME types.
# But most people have a system python already installed so this method is most convenient.
# So here is a list of MIME types for the server to send back per file extension.
# Hopefully this will cover everything.
class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        "": "application/octet-stream",
        ".manifest": "text/cache-manifest",
        ".html": "text/html",
        ".png": "image/png",
        ".jpg": "image/jpg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".css": "text/css",
        ".js": "application/x-javascript",
        ".mjs": "application/x-javascript",
        ".cjs": "application/x-javascript",
        ".wasm": "application/wasm",
        ".json": "application/json",
        ".xml": "application/xml",
        ".xml": "application/xml",
        ".pdf": "application/pdf",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".heic": "image/heic",
        ".heif": "image/heif",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".m4v": "video/mp4",
    }


    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        clean_path = self.path.split("?")[0]
        if clean_path in ("/api/workflows", "/api/workflows/"):
            workflows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")
            list_file = os.path.join(workflows_dir, "list.json")
            if os.path.exists(list_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                with open(list_file, "rb") as f:
                    self.wfile.write(f.read())
                return
        elif clean_path.startswith("/workflows/"):
            fname = clean_path[len("/workflows/"):]
            dist_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows", fname)
            comfy_file = os.path.join("/home/iosage/git/ComfyUI/user/default/workflows", fname)
            if not os.path.exists(dist_file) and os.path.exists(comfy_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                with open(comfy_file, "rb") as f:
                    self.wfile.write(f.read())
                return
        super().do_GET()


socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer((args.listen, args.port), HttpRequestHandler)

try:
    print(message)
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
