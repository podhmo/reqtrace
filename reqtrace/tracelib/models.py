class TracingRequest:
    def __repr__(self):
        return "<{self.__class__.__name__} url={self.url!r}>".format(self=self)

    @property
    def headers(self):
        raise NotImplementedError("dict")

    @property
    def method(self):
        raise NotImplementedError("dict")

    @property
    def body(self):
        raise NotImplementedError("bytes?")


class TracingResponse:
    def __repr__(self):
        return "<{self.__class__.__name__} url={self.url!r}, status_code={self.status_code}>".format(
            self=self
        )

    @property
    def url(self):
        raise NotImplementedError("str")

    @property
    def status_code(self):
        raise NotImplementedError("int")

    @property
    def headers(self):
        raise NotImplementedError("dict")

    @property
    def content(self):
        raise NotImplementedError("bytes?")
