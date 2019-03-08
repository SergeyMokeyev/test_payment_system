import asyncio
import signal
import sys
import logging


class Loop:
    def __init__(self):
        self.__loop = asyncio.get_event_loop()

    def start(self):
        self.__loop.run_forever()

    def stop(self):
        self.__loop.stop()

    @staticmethod
    async def sleep(timeout=0):
        await asyncio.sleep(timeout)

    def create_task(self, task, *args, **kwargs):
        self.__loop.create_task(task(*args, **kwargs))

    def at_signal(self, signum, task, *args, **kwargs):
        self.__loop.add_signal_handler(signum, lambda: asyncio.ensure_future(task(*args, **kwargs)))


class Service:
    def __init__(self, debug=False):
        log_format = '%(asctime)-22s %(levelname)-8s %(message)s'
        datetime_format = '%Y-%m-%d %H:%M:%S'
        logging.basicConfig(format=log_format, datefmt=datetime_format)
        logger = logging.getLogger()
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        self.__logger = logging.getLogger()
        self.__loop = Loop()

    @property
    def loop(self):
        return self.__loop

    @property
    def logger(self):
        return self.__logger

    def start(self):
        self.logger.info('Server started')
        for signum in [signal.SIGINT, signal.SIGTERM]:
            self.loop.at_signal(signum, self.stop)
        self.loop.create_task(self.run)
        self.loop.start()
        sys.exit(0)

    async def stop(self):
        self.logger.info('Server stopped')
        self.loop.stop()

    async def run(self):
        pass
