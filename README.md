### How to:
```
  docker-compose up --build
```

### API docs
```
  http://localhost:8000/docs
```

### Example
Input:
```json
{
  "user_text": "Когда буду в пятерочке и если будет 6 вечера, напомни купить сырки бю александров",
  "current_time": "2025-06-16 10:30"
}
```

Output:
```json
{
  "text": "Купить сырки Б. Ю. Александров",
  "categoryType": "Shopping",
  "triggers": [
    {
      "triggerType": "Location",
      "triggerValue": "Пятёрочка"
    },
    {
      "triggerType": "Time",
      "triggerValue": "2025-06-16 18:00"
    }
  ]
}
```
