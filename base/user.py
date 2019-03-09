class User:
    def __init__(self, data):
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

    @classmethod
    async def load(cls, db, name):
        data = await db.fetchrow("SELECT * FROM users WHERE name = $1", name)
        if data:
            return cls(dict(data))
        raise ValueError('User not found')
