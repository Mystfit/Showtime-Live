import sys
from Logger import Log

NATIVE = False
API = None
_connection = None
_ZST_client = None

if not API:
    try:
        import showtime.showtime as API
        NATIVE = True
    except ImportError:
        Log.write("Couldn't load Showtime native library. Falling back to Showtime RPyC bridge")
        try:
            import rpyc
            _connection = rpyc.connect(
                "localhost", 
                18812, 
                config={"allow_all_attrs": True}
            )
            Log.write = _connection.root.log_write
            sys.stdout = _connection.root.log_write
            sys.stderr = _connection.root.log_write
            API = _connection.root.get_module()
            Log.write("Live connected to RPyC bridge")
        except ImportError as e:
            Log.write("Couldn't load RPyC. Reason: {}".format(e))

def client():
    global _ZST_client
    if not _ZST_client:
        if NATIVE:
            _ZST_client = ZST.ShowtimeClient()
        else:
            _ZST_client = _connection.root.get_client()
    return _ZST_client

def log_memory():
    global _connection
    _connection.root.log_memory()

# def test_adaptor():
#     return _connection.root.test_adaptor_cls()()

def poll():
    global _connection
    _connection.poll_all()

def teleport(func):
    global _connection
    from rpyc.utils.classic import teleport_function
    #return rpyc.utils.classic.teleport_function(_connection, func, [])
    return func
