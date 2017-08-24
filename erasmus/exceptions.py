class DoNotUnderstandError(Exception):
    pass

class BibleNotSupportedError(Exception):
    def __init__(self, version):
        self.version = version

class ServiceNotSupportedError(Exception):
    def __init__(self, service_name):
        self.service_name = service_name
