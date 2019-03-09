CURRENCIES = ['USD', 'EUR', 'CAD', 'CNY']  # todo вынести в настройки системы


class User:
    def __init__(self, db, data):
        self.__db = db
        self.id = data['id']
        self.name = data['name']
        self.country = data['country']
        self.city = data['city']

    def check_sign(self, key=True):
        # todo получать сюда что то для проверки (JWT токен, сертификат, пароль, приватный ключ и тд.) и проверять
        if key:
            return True
        else:
            raise ValueError('Insufficient rights')

    async def get_balance(self):
        balance = {}
        # todo написать нормальный запрос в бд для получения баланса или процедуру в postgres
        for currency in CURRENCIES:
            row = await self.__db.fetchrow("SELECT balance FROM balance "
                                         "WHERE user_id = $1 AND currency = $2 ORDER BY id DESC LIMIT 1",
                                         self.id, currency)
            if not row:
                balance.update({currency: 0})
            else:
                balance.update({currency: row['balance']})

        return balance

    @classmethod
    async def load(cls, db, name):
        data = await db.fetchrow("SELECT * FROM users WHERE name = $1", name)
        if data:
            return cls(db, dict(data))
        raise ValueError('User not found')
