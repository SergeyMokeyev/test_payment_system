import enum
import datetime
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
        while True:  # ждем postgres
            try:
                self.db = await asyncpg.connect(self.__db_url)  # todo здесь бы неплохо пул конектов
                break
            except Exception as exc:
                self.logger.info('Wait postgresql connection')
                await self.loop.sleep(2)

        app = web.Application()
        app.add_routes([
            web.post('/api/v1/', self.api),
            web.post('/reports/', self.reports)
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

            if method is Methods.registration:
                await self.db.execute("INSERT INTO users (name, country, city) VALUES ($1, $2, $3)",
                                      data.get('name'), data.get('country'), data.get('city'))
                message = 'User registered'

            elif method is Methods.recharge:
                currency = request_data.get('currency')
                if currency not in CURRENCIES:
                    raise ValueError('Not allowed currency')

                user = await User.load(self.db, request_data.get('user'))
                user.check_sign()
                amount = data.get('amount', 0)

                tx = Tx(user_id=user.id, operation=Op.debit, currency=currency, amount=amount, db=self.db)
                self.loop.create_task(self.send_to_remote_system, tx)
                message = 'User balance was recharge'

            elif method is Methods.transfer:
                currency = request_data.get('currency')
                if currency not in CURRENCIES:
                    raise ValueError('Not allowed currency')

                amount = data.get('amount', 0)
                from_user = await User.load(self.db, request_data.get('from'))
                from_user.check_sign()
                to_user = await User.load(self.db, request_data.get('to'))

                #### todo много думать
                if currency != 'USD':
                    rate = self.get_rate_from_remote_system()[f'USD_{currency}']
                    _amount = amount / rate
                else:
                    _amount = amount

                to_currency = data.get('currency')
                if to_currency not in CURRENCIES:
                    raise ValueError('Not allowed currency')
                if to_currency != currency:
                    rate = self.get_rate_from_remote_system()[f'USD_{to_currency}']
                    converted_amount = _amount * rate
                else:
                    converted_amount = amount
                ####

                out_tx = Tx(user_id=from_user.id, operation=Op.credit, currency=currency, amount=amount, db=self.db)
                await out_tx.set_status(TxSt.processing)

                await out_tx.set_status(TxSt.accepted)

                in_tx = Tx(user_id=to_user.id, operation=Op.debit,
                           currency=to_currency, amount=converted_amount, db=self.db)
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

    async def reports(self, request):
        try:
            request_data = await request.json()
            user = await User.load(self.db, request_data.get('user'))
            sql = "SELECT tx_id, date, balance, currency, operation  FROM balance WHERE user_id = $1 "
            params = [user.id]

            _to_file = request_data.get('to_file', False)

            _from = datetime.datetime.fromtimestamp(request_data.get('from', 0))
            if _from:
                param = len(params) + 1
                sql = sql + f"AND date >= ${param} "
                params.append(_from)

            _to = datetime.datetime.fromtimestamp(request_data.get('to', datetime.datetime.now().timestamp()))
            if _to:
                param = len(params) + 1
                sql = sql + f"AND date <= ${param} "
                params.append(_to)

            result = []
            for row in await self.db.fetch(sql, *params):
                row = dict(row)
                row['date'] = row['date'].timestamp()
                result.append(row)

            if _to_file:
                # todo делаем файл из result  и отдаем клиенту
                pass
            else:
                return web.json_response({'result': True, 'data': result})

        except ValueError as exc:
            return web.json_response({'result': False, 'error': str(exc)})

        except Exception as exc:
            self.logger.exception(exc)

    async def send_to_remote_system(self, tx):
        # Эмулируем внешнюю систему
        # Отправляем запрос во внешнюю платежную систему на проведение операции ввода денег
        await self.loop.sleep(random.randint(1, 10))
        answer_for_remote_system = random.choice((True, False))
        if answer_for_remote_system:
            # Если Процедура инециализирована то транзакцию в какой то пул и ждем результата транзакции из вне
            await tx.set_status(TxSt.processing)
            await self.loop.sleep(random.randint(1, 10))
            answer_for_remote_system = random.choice((True, False))
            await tx.set_status(TxSt.accepted if answer_for_remote_system else TxSt.failed)
        else:
            await tx.set_status(TxSt.failed)

    @staticmethod
    def get_rate_from_remote_system():
        rate = {
            'USD_USD': 1,
            'USD_EUR': 2,
            'USD_CAD': 3,
            'USD_CNY': 10
        }
        return rate


if __name__ == '__main__':
    Server(
        address='0.0.0.0',
        port=8080,
        db_url='postgresql://postgres:secret@postgres/payments',
        debug=False
    ).start()
