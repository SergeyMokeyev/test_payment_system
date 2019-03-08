import enum


class TransactionOperation(enum.Enum):
    debit = 'debit'
    credit = 'credit'


class TransactionStatus(enum.Enum):
    draft = 'draft'
    processing = 'processing'
    accepted = 'accepted'
    failed = 'failed'


class Transaction:
    def __init__(self, user_id, operation, currency, amount, status=TransactionStatus.draft):
        self.id = None
        self.user_id = user_id
        self.operation = operation
        self.amount = amount
        self.status = status
        self.currency = currency

    async def save(self, db):
        if not self.id:
            self.id = await db.fetchval("INSERT INTO transactions (operation, currency, amount, status, user_id) "
                                        "VALUES ($1, $2, $3, $4, $5) RETURNING id",
                                        self.operation.value, self.currency,
                                        self.amount, self.status.value, self.user_id)
        else:
            pass
