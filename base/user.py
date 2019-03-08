class User:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.country = data['country']
        self.city = data['city']

    @classmethod
    async def load(cls, db, name):
        data = await db.fetchrow("SELECT * FROM users WHERE name = $1", name)
        if data:
            return cls(dict(data))
        raise ValueError('User not found')
