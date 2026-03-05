import json
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

from bson import ObjectId
from app.config import config


class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)
from app.logger import get_logger
from app.routes.router import handle_get, handle_post, handle_put, handle_delete, set_server_started

logger = get_logger("main")

SERVER_STARTED = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
set_server_started(SERVER_STARTED)


class RequestHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", config.CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, cls=MongoEncoder).encode())

    def _send_html(self, status, html):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(html.encode())

    def do_OPTIONS(self):
        logger.info("OPTIONS %s from %s", self.path, self.client_address[0])
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        logger.info("GET %s from %s", self.path, self.client_address[0])
        try:
            content_type, status, data = handle_get(self)
            if content_type == "html":
                self._send_html(status, data)
            else:
                self._send_json(status, data)
            logger.info("GET %s -> %d", self.path, status)
        except Exception as e:
            logger.error("GET %s failed: %s", self.path, e)
            self._send_json(500, {"detail": "Internal server error"})

    def do_POST(self):
        logger.info("POST %s from %s", self.path, self.client_address[0])
        try:
            _, status, data = handle_post(self)
            self._send_json(status, data)
            logger.info("POST %s -> %d", self.path, status)
        except Exception as e:
            logger.error("POST %s failed: %s", self.path, e)
            self._send_json(500, {"detail": "Internal server error"})

    def do_PUT(self):
        logger.info("PUT %s from %s", self.path, self.client_address[0])
        try:
            _, status, data = handle_put(self)
            self._send_json(status, data)
            logger.info("PUT %s -> %d", self.path, status)
        except Exception as e:
            logger.error("PUT %s failed: %s", self.path, e)
            self._send_json(500, {"detail": "Internal server error"})

    def do_DELETE(self):
        logger.info("DELETE %s from %s", self.path, self.client_address[0])
        try:
            _, status, data = handle_delete(self)
            self._send_json(status, data)
            logger.info("DELETE %s -> %d", self.path, status)
        except Exception as e:
            logger.error("DELETE %s failed: %s", self.path, e)
            self._send_json(500, {"detail": "Internal server error"})

    def log_message(self, format, *args):
        logger.info("%s - %s", self.client_address[0], format % args)


if __name__ == "__main__":
    logger.info("Starting server on http://localhost:8000 [%s] env=%s", config.APP_NAME, type(config).__name__)
    server = HTTPServer(("0.0.0.0", 8000), RequestHandler)
    logger.info("Server is ready to accept connections")
    server.serve_forever()
