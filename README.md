# test_payment_system

Запуск в докере
=

Из корня проекта docker-compose build && docker-compose up

API
=
JSON запрос на адрес /api/v1/

- Создание пользователя
```JSON
{"method": "registration", "data": {"name": "petrarka", "country": "Holland", "city": "Amsterdam"}}
```

- Ввод денег в систему из внешней платежной системы
```JSON
{"method": "recharge", "user": "petrarka", "currency": "USD", "data": {"amount": 100}}
```

- Получение баланса
```JSON
{"method": "balance", "user": "petrarka"}
```

- Перевод денег
```JSON
{"method": "transfer", "from": "petrarka", "to": "vasya", "currency": "USD", "data": {"amount": 1.5, "currency": "USD"}}
```

Отчет
=
JSON запрос на адрес /reports/

- Получение отчета
```JSON
{"user": "sergey", "from": 100, "to": 120, "to_file": true}
```