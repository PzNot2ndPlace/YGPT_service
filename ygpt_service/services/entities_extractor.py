import httpx
import json
from fastapi import HTTPException
from pydantic import ValidationError
from typing import Dict, Any, List

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

        prompt = self.build_prompt(options.current_time, options.locations)

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

            if not data["triggers"]:
                data["status"] = "error"
                data["message"] = "Ваше напоминание не содержит условий срабатывания"

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
    def build_prompt(current_time: str, locations: List[str]) -> str:
        known_locations = ", ".join(f'"{loc}"' for loc in locations) if locations else "нет известных мест"
        return f"""
        Ты — AI-ассистент для создания напоминаний. Разбирай команды пользователя, используя:
        - Текущее время: {current_time}
        - Известные локации пользователя: {known_locations}

        Возвращай JSON строго в таком формате:
        {{
            "text": "текст напоминания",
            "categoryType": "одно из допустимых значений",
            "triggers": [
                {{
                    "triggerType": "одно из допустимых значений",
                    "triggerValue": "конкретное время/место/событие"
                }}
            ],
            "status": "success" или "error",
            "message": "описание проблемы (если status=error)"
        }}

        ### Допустимые значения:
        - `categoryType`: Time, Location, Event, Shopping, Call, Meeting, Deadline, Health, Routine, Other  
        - `triggerType`: Time, Location

        ### Важные правила:
        1. Для триггеров типа Location:
           - Используй ТОЛЬКО локации из известного списка: {known_locations}
           - Если локация не найдена в списке, верни status=error и сообщи об этом
        2. Для времени:
           - "в 18:00" → Time (преобразуй в абсолютное время, используя {current_time})  
           - "через 2 часа" → Time (вычисли: {current_time} + 2 часа)  
        3. Если команда неполная, верни status=error с пояснением

        ### Пример 1 (известные локации: "дом", "парк")
        Команда: "напомни погулять с собакой когда буду в парке"
        Вывод:
        {{
            "text": "Погулять с собакой",
            "categoryType": "Routine",
            "triggers": [
                {{
                    "triggerType": "Location",
                    "triggerValue": "парк"
                }}
            ],
            "status": "success",
            "message": ""
        }}

        ### Пример 2 (известные локации: "дом", "офис")
        Команда: "напомни купить молоко когда буду в магазине"
        Вывод:
        {{
            "text": "",
            "categoryType": "Other",
            "triggers": [],
            "status": "error",
            "message": "Локация 'магазин' не найдена в ваших известных местах"
        }}

        ### Пример 3 (известные локации: "дом")
        Команда: "Когда буду в пятерочке и если будет 6 вечера, напомни купить сырки бю александров"
        Вывод:
        {{
            "text": "Купить сырки Б. Ю. Александров",
            "categoryType": "Shopping",
            "triggers": [
                {{
                  "triggerType": "Location",
                  "triggerValue": "Пятёрочка"
                }},
                {{
                  "triggerType": "Time",
                  "triggerValue": "2025-06-16 18:00"
                }}
            ]
            "message": ""
        }}

        Теперь разбери команду пользователя (текущее время: {current_time}, известные локации: {known_locations}):
        """


entities_extractor = EntitiesExtractorService()
