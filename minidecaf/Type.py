class MiniDecafType:
    def __init__(self, name):
        self.name = name


class NoType(MiniDecafType):
    def __init__(self):
        super().__init__("NoType")


class IntType(MiniDecafType):
    def __init__(self):
        super().__init__("IntType")
