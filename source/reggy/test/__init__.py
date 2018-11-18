from typing import IO


class StreamUtility:
    @staticmethod
    def data(stream: IO) -> str:
        stream.seek(0)
        return ''.join([line for line in stream])
