import asyncio
import os

import httpx

URL = os.environ["SSE_URL"]

cookies = {
    "access_token": os.environ["ACCESS_TOKEN"],
    "refresh_token": os.environ["REFRESH_TOKEN"],
}


async def main():
    async with httpx.AsyncClient(
        cookies=cookies,
        timeout=None,
    ) as client, client.stream(
        "GET",
        URL,
        headers={"Accept": "text/event-stream"},
    ) as response:
        print("Status:", response.status_code)
        print("Headers:", response.headers)

        if response.status_code != 200:
            print(await response.aread())
            return

        async for line in response.aiter_lines():
            print(repr(line))


if __name__ == "__main__":
    asyncio.run(main())
