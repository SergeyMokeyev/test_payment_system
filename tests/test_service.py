import unittest
import asyncio
import logging

from base.service import Service, Loop


class ServiceTests(unittest.TestCase):

    async def _test_service(self):
        service = Service()

        self.assertIsInstance(service.loop, Loop)
        self.assertIsInstance(service.logger, logging.Logger)


    def test_err_tx(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_service())


if __name__ == '__main__':
    unittest.main()
