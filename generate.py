class TextGenerateBase:
    def __init__(self, body):
        raise NotImplementedError

    def stream_generate(self):
        raise NotImplementedError

    def generate(self):
        raise NotImplementedError

    def token_count(self):
        raise NotImplementedError
