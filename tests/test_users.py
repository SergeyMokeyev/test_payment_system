import unittest
import asyncio

from base.user import User


class TransactionMock:

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def __aenter__(self):
        pass

    async def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class DataBaseMock:

    transaction = TransactionMock

    async def execute(self, *_, **__):
        return True

    async def fetchrow(self, _, name):
        if name == 'petrarka':
            return {
                'id': 1,
                'name': 'petrarka',
                'country': 'Holand',
                'city': 'Amsterdam'
            }
        else:
            raise Exception()


db = DataBaseMock()


class UsersTests(unittest.TestCase):

    async def _test_users(self):
        user = await User.load(db, 'petrarka')

        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, 'petrarka')

        with self.assertRaises(Exception):
            user = await User.load(db, 'vasya')

    def test_err_tx(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_users())


if __name__ == '__main__':
    unittest.main()
