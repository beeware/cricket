import asyncio
import unittest
from unittest.mock import patch

from cricket.executor import Executor


class FakeStream:
    async def readline(self):
        return b""


class FakeProcess:
    stdout = FakeStream()
    stderr = FakeStream()


class FakeTestSuite:
    def execute_commandline(self, labels):
        return ["python", "-m", "cricket.unittest.executor"] + labels


class ExecutorTests(unittest.TestCase):
    def test_subprocess_uses_unbuffered_binary_pipes(self):
        kwargs = {}

        async def create_subprocess_shell(command, **received_kwargs):
            kwargs.update(received_kwargs)
            return FakeProcess()

        executor = Executor(FakeTestSuite())

        with patch("asyncio.create_subprocess_shell", create_subprocess_shell):
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(executor.run(count=0, labels=["tests"]))
            finally:
                loop.close()

        self.assertIn("bufsize", kwargs)
        self.assertEqual(kwargs["bufsize"], 0)


if __name__ == "__main__":
    unittest.main()
