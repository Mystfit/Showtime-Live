# Message prefixes

class PyroPrefixes:
    INCOMING = "I"
    OUTGOING = "O"
    RESPONDER = "L"
    # PASSTHROUGH = "P"
    REGISTRATION = "R"
    DELIMITER = "_"

    @staticmethod
    def prefix_outgoing(name):
        return PyroPrefixes.OUTGOING + PyroPrefixes.prefix_name(name)

    @staticmethod
    def prefix_incoming(name):
        return PyroPrefixes.INCOMING + PyroPrefixes.prefix_name(name)

    @staticmethod
    def prefix_responder(name):
        return PyroPrefixes.RESPONDER + PyroPrefixes.prefix_name(name)
    
    # @staticmethod
    # def prefix_passthrough(name):
    #     return PyroPrefixes.PASSTHROUGH + PyroPrefixes.prefix_name(name)
    
    @staticmethod
    def prefix_registration(name):
        return PyroPrefixes.REGISTRATION + PyroPrefixes.prefix_name(name)

    @staticmethod
    def prefix_name(name):
        return PyroPrefixes.DELIMITER + name
