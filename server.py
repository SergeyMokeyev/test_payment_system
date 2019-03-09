import enum
import random

import asyncpg
from aiohttp import web

from base.service import Service
from base.user import User
from base.transaction import Transaction as Tx, TransactionOperation as Op, TransactionStatus as TxSt


CURRENCIES = ['USD', 'EUR', 'CAD', 'CNY']  # todo вынести в настройки системы


class Methods(enum.Enum):
    registration = 'registration'
    recharge = 'recharge'
    transfer = 'transfer'
    balance = 'balance'


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

            if method is not Methods.registration and method is not Methods.balance:  # todo с этим нужно что то делать
                currency = request_data.get('currency')
                if currency not in CURRENCIES:
                    raise ValueError('Not allowed currency')

            if method is Methods.registration:
                await self.db.execute("INSERT INTO users (name, country, city) VALUES ($1, $2, $3)",
                                      data.get('name'), data.get('country'), data.get('city'))
                message = 'User registered'

            elif method is Methods.recharge:
                user = await User.load(self.db, request_data.get('user'))
                user.check_sign()
                amount = data.get('amount', 0)

                tx = Tx(user_id=user.id, operation=Op.debit, currency=currency, amount=amount, db=self.db)
                self.loop.create_task(self.send_to_remote_system, tx)
                message = 'User balance was recharge'

            elif method is Methods.transfer:
                amount = data.get('amount', 0)
                from_user = await User.load(self.db, request_data.get('from'))
                from_user.check_sign()
                to_user = await User.load(self.db, request_data.get('to'))

                # todo тут бум конвертировать валюту

                out_tx = Tx(user_id=from_user.id, operation=Op.credit, currency=currency, amount=amount, db=self.db)
                await out_tx.set_status(TxSt.processing)

                await out_tx.set_status(TxSt.accepted)

                in_tx = Tx(user_id=to_user.id, operation=Op.debit, currency=currency, amount=amount, db=self.db)
                await in_tx.set_status(TxSt.accepted)

                message = 'Transfer successful'

            elif method is Methods.balance:
                user = await User.load(self.db, request_data.get('user'))
                user.check_sign()
                message = await user.get_balance()

            response = {'result': True, 'message': message}
            self.logger.debug('Response to %s, data: %s', request.remote, response)
            return web.json_response(response)

        except ValueError as exc:
            return web.json_response({'result': False, 'error': str(exc)})

        except Exception as exc:
            self.logger.exception(exc)
            return web.json_response({'result': False, 'error': 'Something was wrong'})

    async def send_to_remote_system(self, tx):
        # await self.loop.sleep(random.randint(1, 10))
        # answer_for_remote_system = random.choice((True, False))
        answer_for_remote_system = True
        if answer_for_remote_system:
            await tx.set_status(TxSt.processing)
            # await self.loop.sleep(random.randint(1, 10))
            # answer_for_remote_system = random.choice((True, False))
            answer_for_remote_system = True
            await tx.set_status(TxSt.accepted if answer_for_remote_system else TxSt.failed)
        else:
            await tx.set_status(TxSt.failed)


if __name__ == '__main__':
    Server(
        address='0.0.0.0',
        port=8080,
        db_url='postgresql://postgres:secret@localhost/payments',
        debug=True
    ).start()
