import os
import ssl

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    if os.getenv("CS3900_ENV") == "production":
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(keyfile="/usr/src/ssl/tls.key", certfile="/usr/src/ssl/tls.crt")
        uvicorn.run(app, host="0.0.0.0", port=8443, log_level="warning", ssl_keyfile="/usr/src/ssl/tls.key", ssl_certfile="/usr/src/ssl/tls.crt")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
