"""
Vercel Serverless Function for FastAPI backend.
Uses BaseHTTPRequestHandler bridge to ASGI.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import asyncio
import sys
import os

# Add parent directory for src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app for serverless
app = FastAPI(title="Todo Backend API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "Todo Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "environment": "vercel-serverless"}

@app.get("/api/v1/health")
def api_health():
    return {"status": "healthy", "version": "1.0.0"}

# Simple sync handler bridge
class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Route to appropriate endpoint
        if path == "/" or path == "":
            response = root()
        elif path == "/health":
            response = health()
        elif path == "/api/v1/health":
            response = api_health()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found", "path": path}).encode())
            return

        self._set_headers(200)
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        self._set_headers(501)
        self.wfile.write(json.dumps({"error": "POST not implemented in serverless mode"}).encode())

    def do_PUT(self):
        self._set_headers(501)
        self.wfile.write(json.dumps({"error": "PUT not implemented in serverless mode"}).encode())

    def do_DELETE(self):
        self._set_headers(501)
        self.wfile.write(json.dumps({"error": "DELETE not implemented in serverless mode"}).encode())
