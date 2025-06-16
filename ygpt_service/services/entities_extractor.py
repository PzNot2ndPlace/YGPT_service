import httpx
import json
from fastapi import HTTPException
from pydantic import ValidationError
from typing import Dict, Any

from ygpt_service.constants import *
from ygpt_service.schemas import GenerateTextRequest


class EntitiesExtractorService:
    def __init__(self):
        if not IAM or not FOLDER_ID:
            print("Warning: IAM or FOLDER_ID not set")
        self.ygpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Authorization": f"Bearer {IAM}",
            "x-folder-id": FOLDER_ID,
            "Content-Type": "application/json"
        }

    async def extract_entities_from_user_text(self, options: GenerateTextRequest) -> Dict[str, Any]:
        """Вычленение важной для бэкенда информации с помощью API YandexGPT"""
        if not IAM or not FOLDER_ID:
            raise HTTPException(
                status_code=500,
                detail="API key for AI service (text) is not configured"
            )

        prompt = self.build_prompt(options.current_time)

        request_data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 1000
            },
            "messages": [
                {
                    "role": "system",
                    "text": prompt
                },
                {
                    "role": "user",
                    "text": f"Команда: {options.user_text}"
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.ygpt_url,
                    headers=self.headers,
                    json=request_data
                )
                response.raise_for_status()

                result = response.json()
                llm_output = result['result']['alternatives'][0]['message']['text'].replace('`', '')

                print(llm_output)

                # Валидация ответа
                try:
                    data = json.loads(llm_output)
                    validated_data = self.validate_response(data)
                    return validated_data
                except (json.JSONDecodeError, ValidationError) as e:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid LLM response format: {str(e)}"
                    )

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"YandexGPT API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Text processing failed: {str(e)}"
            )

    @staticmethod
    def validate_response(data: Dict) -> Dict:
        """Валидация структуры ответа от LLM"""
        try:
            # Проверка обязательных полей
            if not all(key in data for key in ["text", "categoryType", "triggers"]):
                raise ValueError("Missing required fields in response")

            # Проверка допустимых значений categoryType
            valid_categories = {"Time", "Location", "Event", "Shopping", "Call",
                                "Meeting", "Deadline", "Health", "Routine", "Other"}
            if data["categoryType"] not in valid_categories:
                raise ValueError(f"Invalid categoryType: {data['categoryType']}")

            # Проверка триггеров
            for trigger in data["triggers"]:
                if not all(key in trigger for key in ["triggerType", "triggerValue"]):
                    raise ValueError("Trigger missing required fields")
                if trigger["triggerType"] not in {"Time", "Location"}:
                    raise ValueError(f"Invalid triggerType: {trigger['triggerType']}")

            return data

        except Exception as e:
            raise ValueError(f"Response validation failed: {str(e)}")

    @staticmethod
    def build_prompt(current_time: str) -> str:
        return f"""
        Ты — AI-ассистент для создания напоминаний. Разбирай команды пользователя, используя текущее время: {current_time}. 
        Возвращай JSON строго в таком формате:
        {{
            "text": "текст напоминания",
            "categoryType": "одно из допустимых значений",
            "triggers": [
                {{
                    "triggerType": "одно из допустимых значений",
                    "triggerValue": "конкретное время/место/событие"
                }}
            ]
        }}

        ### Допустимые значения:
        - `categoryType`: Time, Location, Event, Shopping, Call, Meeting, Deadline, Health, Routine, Other  
        - `triggerType`: Time, Location  

        ### Правила:
        1. `categoryType` определяется по смыслу напоминания:
           - "купить молоко" → Shopping  
           - "позвонить маме" → Call  
           - "встреча в кафе" → Meeting  
        2. `triggerType` зависит от условия:
           - "в 18:00" → Time (преобразуй в абсолютное время, используя {current_time})  
           - "через 2 часа" → Time (вычисли: {current_time} + 2 часа)  
           - "когда буду в Пятёрочке" → Location  
        3. Для относительного времени (e.g., "завтра", "через час") всегда указывай абсолютное время в формате "YYYY-MM-DD HH:MM".

        ### Пример 1 (с текущим временем {current_time} = "2025-06-16 15:00"):
        Команда: "Напомни выгулить собаку через 3 часа"
        Вывод:
        {{
            "text": "Выгулить собаку",
            "categoryType": "Routine",
            "triggers": [
                {{
                    "triggerType": "Time",
                    "triggerValue": "2025-06-16 18:00"
                }}
            ]
        }}

        ### Пример 2 (с текущим временем {current_time} = "2025-06-16 09:00"):
        Команда: "Завтра в 10:00 напомни позвонить врачу"
        Вывод:
        {{
            "text": "Позвонить врачу",
            "categoryType": "Health",
            "triggers": [
                {{
                    "triggerType": "Time",
                    "triggerValue": "2025-06-17 10:00"
                }}
            ]
        }}

        Теперь разбери команду пользователя (текущее время: {current_time}):
        """


entities_extractor = EntitiesExtractorService()
