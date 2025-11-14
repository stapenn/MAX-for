# mybot.py
import mimetypes
import asyncio
import httpx

from typing import Optional
from maxbot.bot import Bot as BaseBot
from maxbot.types import InlineKeyboardMarkup


class Bot(BaseBot):
    async def upload_file(self, file_path: str, media_type: str) -> str:
        # 1. Получаем URL загрузки (это уже умеет BaseBot._request)
        resp = await self._request("POST", "/uploads", params={"type": media_type})
        upload_url = resp["url"]

        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            files = {"data": (file_path, f, mime_type or "application/octet-stream")}
            async with httpx.AsyncClient() as client:
                upload_resp = await client.post(upload_url, files=files)
                upload_resp.raise_for_status()

                print("[DEBUG] upload_resp.status_code:", upload_resp.status_code)
                print("[DEBUG] upload_resp.text:", upload_resp.text)

                # 🔧 ВАЖНО: НИКАКИХ <retval>, сразу json()
                try:
                    result = upload_resp.json()
                except ValueError:
                    raise ValueError(
                        f"Не удалось распарсить JSON в ответе от сервера: {upload_resp.text}"
                    )

        # 2. Извлекаем токен (новый формат ответа от MAX)
        token = result.get("token")
        if not token:
            raise ValueError(f"Не найден токен в ответе: {result}")
        return token

    async def send_file(
        self,
        file_path: str,
        media_type: str,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        text: str = "",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        notify: bool = True,
        format: Optional[str] = None,
        max_retries: int = 3,
    ):
        # 1. Загружаем файл и получаем token
        token = await self.upload_file(file_path, media_type)
        await asyncio.sleep(1)  # небольшая задержка, чтобы файл "подхватился" на стороне MAX

        attachments = [
            {
                "type": media_type,
                "payload": {"token": token},
            }
        ]
        if reply_markup:
            attachments.append(reply_markup.to_attachment())

        params = {
            "access_token": self.token,
        }
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        json_body = {
            "text": text,
            "notify": notify,
            "attachments": attachments,
        }
        if format:
            json_body["format"] = format

        print("[send_file] params:", params)
        print("[send_file] json:", json_body)

        delay = 2
        resp = None
        for attempt in range(1, max_retries + 1):
            resp = await self.client.post(
                f"{self.base_url}/messages",
                params=params,
                json=json_body,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            print(f"Attempt {attempt}: RESP:", resp.status_code)
            print("RESP_TEXT:", resp.text)

            if resp.status_code != 400:
                return resp

            if "attachment.not.ready" in resp.text or "not.processed" in resp.text:
                print(f"Жду {delay} секунд и пробую ещё раз...")
                await asyncio.sleep(delay)
            else:
                break

        return resp
