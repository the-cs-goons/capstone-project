import asyncio
import os

import uvicorn


async def serve_app(app: str, port_env: int):
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=int(os.getenv(port_env)),
        log_level="debug",
        ssl_certfile="examples/example_ssl_certfile.crt",
        ssl_keyfile="examples/example_ssl_keyfile.key",
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    apps = [
        asyncio.create_task(
            serve_app(
                app="examples.bar_demo_agent:verifier_server",
                port_env="CS3900_BAR_VERIFIER_DEMO_AGENT_PORT",
            )
        ),
        asyncio.create_task(
            serve_app(
                app="examples.car_rental_demo_agent:verifier_server",
                port_env="CS3900_CAR_RENTAL_VERIFIER_DEMO_AGENT_PORT",
            )
        ),
    ]

    _, pending_tasks = await asyncio.wait(apps, return_when=asyncio.FIRST_COMPLETED)
    for pending_task in pending_tasks:
        pending_task.cancel("Another task crashed")


if __name__ == "__main__":
    asyncio.run(main())
