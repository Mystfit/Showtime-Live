# Message prefixes

class PyroPrefixes:
    INCOMING = "I"
    OUTGOING = "O"
    REGISTRATION = "R"
    DELIMITER = "_"

    @staticmethod
    def prefix_outgoing(name):
        return PyroPrefixes.INCOMING + PyroPrefixes.prefix_name(name)
    @staticmethod
    def prefix_incoming(name):
        return PyroPrefixes.OUTGOING + PyroPrefixes.prefix_name(name)

    @staticmethod
    def prefix_registration(name):
        return PyroPrefixes.REGISTRATION + PyroPrefixes.prefix_name(name)

    @staticmethod
    def prefix_name(name):
        return PyroPrefixes.DELIMITER + name
