### How to:
```
  docker-compose up --build
```

### API docs
```
  http://localhost:8000/docs
```

### Example 1
Input:
```json
{
  "user_text": "Когда буду в пятерочке и если будет 6 вечера, напомни купить сырки бю александров",
  "current_time": "2025-06-16 10:30",
  "locations": ["пятерочка", "дом", "работа"]
}
```

Output:
```json
{
  "text": "Купить сырки 'бю александров'",
  "categoryType": "Shopping",
  "triggers": [
    {
      "triggerType": "Location",
      "triggerValue": "пятерочка"
    },
    {
      "triggerType": "Time",
      "triggerValue": "2025-06-16 18:00"
    }
  ],
  "status": "success",
  "message": ""
}
```


### Example 2
Input:
```json
{
  "user_text": "Когда буду в пятерочке и если будет 6 вечера, напомни купить сырки бю александров",
  "current_time": "2025-06-16 10:30",
  "locations": ["дом", "работа"]
}
```

Output:
```json
{
  "text": "Купить сырки 'Б.Ю. Александров'",
  "categoryType": "Shopping",
  "triggers": [
    {
      "triggerType": "Location",
      "triggerValue": "пятерочка"
    },
    {
      "triggerType": "Time",
      "triggerValue": "2025-06-16 18:00"
    }
  ],
  "status": "error",
  "message": "Локация 'пятерочка' не найдена в ваших известных местах" 
}
```

### Example 3
Input:
```json
{
  "user_text": "тралалело тралала",
  "current_time": "2025-06-16 10:30",
  "locations": ["дом", "работа"]
}
```

Output:
```json
{
  "text": "",
  "categoryType": "Other",
  "triggers": [],
  "status": "error",
  "message": "Команда неполная и не содержит достаточно информации для создания напоминания"
}
```

# А еще теперь это МОЯ ЛАБА ПО КИБЕРБЕЗУ
так что...

### 1. Статический анализ кода (SAST)
```
bandit -r ./
```

<img src="https://github.com/PzNot2ndPlace/YGPT_service/blob/develop/images/1..png">
<img src="https://github.com/PzNot2ndPlace/YGPT_service/blob/develop/images/Снимок%20экрана%202025-06-20%20003810.png">
