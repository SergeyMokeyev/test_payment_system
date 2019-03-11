import unittest
import asyncio

from base.transaction import Transaction, TransactionOperation, TransactionStatus


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

    async def fetchval(self, *_, **__):
        return True


db = DataBaseMock()


class TransactionsTests(unittest.TestCase):

    def test_tx_op(self):
        self.assertIsInstance(TransactionOperation('debit'), TransactionOperation)

    def test_tx_err_op(self):
        with self.assertRaises(ValueError):
            TransactionOperation('wrong_op')

    def test_tx_status(self):
        self.assertIsInstance(TransactionStatus('draft'), TransactionStatus)

    def test_tx_err_status(self):
        with self.assertRaises(ValueError):
            TransactionOperation('wrong_status')

    async def _test_tx(self):
        tx = Transaction(99, TransactionOperation.debit, 'EUR', 999, db=db)
        self.assertEqual(tx.status, TransactionStatus.draft)

        await tx.set_status(TransactionStatus.processing)
        self.assertEqual(tx.status, TransactionStatus.processing)

    def test_tx(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_tx())

    async def _test_err_tx(self):
        with self.assertRaises(AttributeError):
            Transaction(99, 'debit', 'EUR', 999, db=db)

        tx = Transaction(99, TransactionOperation.credit, 'EUR', 999, db=db)
        with self.assertRaises(AttributeError):
            await tx.set_status('processing')

        with self.assertRaises(AttributeError):
            Transaction(99, TransactionOperation.credit, 'RUB', 999, db=db)

    def test_err_tx(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_tx())


if __name__ == '__main__':
    unittest.main()
