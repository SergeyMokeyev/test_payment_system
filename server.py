import enum
import random

import asyncpg
from aiohttp import web

from base.service import Service
from base.user import User
from base.transaction import Transaction as Tx, TransactionOperation as Op


CURRENCIES = ['USD', 'EUR', 'CAD', 'CNY']


class Methods(enum.Enum):
    registration = 'registration'
    recharge = 'recharge'


class Server(Service):
    def __init__(self, address, port, db_url, debug=False):
        super().__init__(debug=debug)
        self.__address = address
        self.__port = port
        self.__db_url = db_url

    async def run(self):
        self.db = await asyncpg.connect(self.__db_url)

        app = web.Application()
        app.add_routes([
            web.post('/api/v1/', self.api)
        ])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host=self.__address,
            port=self.__port
        )
        await site.start()
        self.logger.info('Listen %s:%s', self.__address, self.__port)

    async def api(self, request):
        try:
            request_data = await request.json()
            self.logger.debug('Request from %s, data: %s', request.remote, request_data)

            method = Methods(request_data.get('method'))
            data = request_data.get('data', {})
            currency = request_data.get('currency')
            user = await User.load(self.db, request_data.get('user'))

            if currency not in CURRENCIES:
                raise ValueError('Not allowed currency')

            if method is Methods.registration:
                await self.db.execute("INSERT INTO users (name, country, city, currency) VALUES ($1, $2, $3, $4)",
                                      data.get('name'), data.get('country'), data.get('city'), currency)
                message = 'User registered'

            elif method is Methods.recharge:
                amount = data.get('amount', 0)
                tx = Tx(user_id=user.id, operation=Op.debit, currency=currency, amount=amount)
                await tx.save(self.db)
                self.loop.create_task(self.send_to_remote_system, tx)
                message = 'User balance was recharge'

            response = {'result': True, 'message': message}
            self.logger.debug('Response to %s, data: %s', request.remote, response)
            return web.json_response(response)

        except Exception as exc:
            self.logger.exception(exc)
            return web.json_response({'result': False, 'error': str(exc)})

    async def send_to_remote_system(self, tx):
        await self.loop.sleep(random.randint(1, 10))
        print(tx)


if __name__ == '__main__':
    Server(
        address='0.0.0.0',
        port=8080,
        db_url='postgresql://postgres:secret@localhost/payments',
        debug=True
    ).start()
