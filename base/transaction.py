import enum
import logging


class TransactionOperation(enum.Enum):
    debit = 'debit'
    credit = 'credit'


class TransactionStatus(enum.Enum):
    draft = 'draft'
    processing = 'processing'
    accepted = 'accepted'
    failed = 'failed'


class Transaction:
    def __init__(self, user_id, operation, currency, amount, db=None):
        self.id = None
        self.user_id = user_id
        self.operation = operation
        self.amount = amount
        self.currency = currency
        self.db = db
        self.status = TransactionStatus.draft
        self.__reserved = None

    async def set_status(self, value):
        await self.__save_to_db()

        self.status = value

        if self.operation is TransactionOperation.credit:
            if self.status is TransactionStatus.processing:
                balance, reserved = await self.__get_balance()
                if balance < self.amount:
                    raise ValueError('Insufficient balance')

                balance -= self.amount
                reserved += self.amount
                self.__reserved = self.amount
                await self.__set_balance(balance, reserved)
                logging.info('User id %s begin withdraw, reserved %s', self.user_id, self.__reserved)

            elif self.status is TransactionStatus.accepted:
                balance, reserved = await self.__get_balance()
                if self.__reserved > reserved:
                    raise ValueError('Insufficient reserved')

                reserved -= self.__reserved
                self.__reserved = None
                await self.__set_balance(balance, reserved)
                logging.info('User id %s finish withdraw', self.user_id)

            elif self.status is TransactionStatus.failed:
                if self.__reserved:
                    balance, reserved = await self.__get_balance()
                    reserved -= self.__reserved
                    self.__reserved = None
                    await self.__set_balance(balance, reserved)
                logging.info('User id %s failed withdraw', self.user_id)

        elif self.operation is TransactionOperation.debit:
            if self.status is TransactionStatus.accepted:
                async with self.db.transaction():
                    balance, reserved = await self.__get_balance()
                    balance += self.amount
                    await self.__set_balance(balance, reserved)
                    logging.info('User id %s balance was recharge', self.user_id)

        else:
            raise ValueError('Wrong operation')

        await self.__save_to_db()

    async def __get_balance(self):
        row = await self.db.fetchrow("SELECT balance, reserved "
                                     "FROM balance WHERE user_id = $1 AND currency = $2 ORDER BY id DESC LIMIT 1",
                                     self.user_id, self.currency)
        if not row:
            return 0, 0
        else:
            return row['balance'], row['reserved']

    async def __set_balance(self, balance, reserved):
        await self.db.execute("INSERT INTO balance (tx_id, user_id, balance, reserved, currency, operation) "
                              "VALUES ($1, $2, $3, $4, $5, $6)", self.id, self.user_id, balance, reserved,
                              self.currency, self.operation.value)

    async def __save_to_db(self):
        if not self.id:
            async with self.db.transaction():
                self.id = await self.db.fetchval("INSERT INTO transactions "
                                                 "(operation, currency, amount, status, user_id) "
                                                 "VALUES ($1, $2, $3, $4, $5) RETURNING id",
                                                 self.operation.value, self.currency,
                                                 self.amount, self.status.value, self.user_id)
        else:
            async with self.db.transaction():
                await self.db.execute("UPDATE transactions SET status = $1 WHERE id = $2", self.status.value, self.id)
