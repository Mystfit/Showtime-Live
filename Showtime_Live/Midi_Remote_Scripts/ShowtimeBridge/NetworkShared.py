# Message prefixes

class NetworkPrefixes:
    INCOMING = "I"
    OUTGOING = "O"
    RESPONDER = "L"
    # PASSTHROUGH = "P"
    REGISTRATION = "R"
    DELIMITER = "_"

    @staticmethod
    def prefix_outgoing(name):
        return NetworkPrefixes.OUTGOING + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_incoming(name):
        return NetworkPrefixes.INCOMING + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_responder(name):
        return NetworkPrefixes.RESPONDER + NetworkPrefixes.prefix_name(name)
    
    # @staticmethod
    # def prefix_passthrough(name):
    #     return NetworkPrefixes.PASSTHROUGH + NetworkPrefixes.prefix_name(name)
    
    @staticmethod
    def prefix_registration(name):
        return NetworkPrefixes.REGISTRATION + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_name(name):
        return NetworkPrefixes.DELIMITER + name
