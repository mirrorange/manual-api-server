import json
import traceback
import completions
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from errors import InvalidRequestError, OpenAIError
from models import get_engine, get_model, get_model_list


class Handler(BaseHTTPRequestHandler):
    def send_access_control_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Origin, Accept, X-Requested-With, Content-Type, "
            "Access-Control-Request-Method, Access-Control-Request-Headers, "
            "Authorization",
        )

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_access_control_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write("OK".encode("utf-8"))

    def start_sse(self):
        self.send_response(200)
        self.send_access_control_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        # self.send_header('Connection', 'keep-alive')
        self.end_headers()

    def send_sse(self, chunk: dict):
        response = "data: " + json.dumps(chunk) + "\r\n\r\n"
        self.wfile.write(response.encode("utf-8"))

    def end_sse(self):
        response = "data: [DONE]\r\n\r\n"
        self.wfile.write(response.encode("utf-8"))

    def return_json(self, ret: dict, code: int = 200):
        self.send_response(code)
        self.send_access_control_headers()
        self.send_header("Content-Type", "application/json")

        response = json.dumps(ret)
        r_utf8 = response.encode("utf-8")

        self.send_header("Content-Length", str(len(r_utf8)))
        self.end_headers()

        self.wfile.write(r_utf8)

    def openai_error(
        self, message, code=500, error_type="APIError", param="", internal_message=""
    ):
        error_resp = {
            "error": {
                "message": message,
                "code": code,
                "type": error_type,
                "param": param,
            }
        }
        if internal_message:
            print(error_type, message)
            print(internal_message)

        self.return_json(error_resp, code)

    def openai_error_handler(func):
        def wrapper(self):
            try:
                func(self)
            except InvalidRequestError as e:
                self.openai_error(
                    e.message,
                    e.code,
                    e.__class__.__name__,
                    e.param,
                    internal_message=e.internal_message,
                )
            except OpenAIError as e:
                self.openai_error(
                    e.message,
                    e.code,
                    e.__class__.__name__,
                    internal_message=e.internal_message,
                )
            except Exception as e:
                self.openai_error(
                    repr(e), 500, "OpenAIError", internal_message=traceback.format_exc()
                )

        return wrapper

    @openai_error_handler
    def do_GET(self):
        if self.path.startswith("/v1/engines") or self.path.startswith("/v1/models"):
            is_legacy = "engines" in self.path
            is_list = self.path in ["/v1/engines", "/v1/models"]
            if is_legacy and not is_list:
                model_name = self.path[
                    self.path.find("/v1/engines/") + len("/v1/engines/") :
                ]
                resp = get_engine(model_name)
            elif is_list:
                resp = get_model_list(is_legacy)
            else:
                model_name = self.path[len("/v1/models/") :]
                resp = get_model(model_name)

            self.return_json(resp)

        elif "/billing/usage" in self.path:
            self.return_json({"total_usage": 0})

        else:
            self.send_error(404)

    @openai_error_handler
    def do_POST(self):
        content_length = self.headers.get("Content-Length")
        transfer_encoding = self.headers.get("Transfer-Encoding")

        if content_length:
            body = json.loads(self.rfile.read(int(content_length)).decode("utf-8"))
        elif transfer_encoding == "chunked":
            chunks = []
            while True:
                chunk_size = int(self.rfile.readline(), 16)  # Read the chunk size
                if chunk_size == 0:
                    break  # End of chunks
                chunks.append(self.rfile.read(chunk_size))
                self.rfile.readline()  # Consume the trailing newline after each chunk
            body = json.loads(b"".join(chunks).decode("utf-8"))
        else:
            self.send_response(
                400,
                "Bad Request: Either Content-Length or Transfer-Encoding header expected.",
            )
            self.end_headers()
            return

        if "/completions" in self.path or "/generate" in self.path:
            is_legacy = "/generate" in self.path
            is_streaming = body.get("stream", False)

            if is_streaming:
                self.start_sse()

                response = []
                if "chat" in self.path:
                    response = completions.stream_chat_completions(
                        body, is_legacy=is_legacy
                    )
                else:
                    self.send_error(404)

                for resp in response:
                    self.send_sse(resp)

                self.end_sse()

            else:
                response = ""
                if "chat" in self.path:
                    response = completions.chat_completions(
                        body, is_legacy=is_legacy
                    )
                else:
                    self.send_error(404)

                self.return_json(response)

        else:
            self.send_error(404)


def run_server():
    server_addr = ("127.0.0.1", 8080)
    server = ThreadingHTTPServer(server_addr, Handler)
    print(
        f"OpenAI compatible API ready at: OPENAI_API_BASE=http://{server_addr[0]}:{server_addr[1]}/v1"
    )
    server.serve_forever()


if __name__ == "__main__":
    run_server()
