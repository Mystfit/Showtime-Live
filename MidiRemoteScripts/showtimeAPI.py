import sys
from ShowtimeLive.Logger import Log

NATIVE = False
API = None
_connection = None
_ZST_client = None

# Manual showtime import to test import errors
# import showtime.showtime
# raise Exception(dir(showtime.showtime))


if not API:
    try:
        # import showtime.showtime as API
        # NATIVE = True
        raise ImportError("Skipping native Showtime")
    except ImportError as err:
        Log.write("Couldn't load Showtime native library. Attempting to use RPyC")
        try:
            import rpyc
            _connection = rpyc.connect(
                b"localhost", 
                18812, 
                config={"allow_all_attrs": True},
            )
            Log.set_logger(_connection.root.log_write)
            # sys.stdout = _connection.root.log_write
            # sys.stderr = _connection.root.log_write
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

def set_control_surface(control_surface):
    _connection.root.set_control_surface_callback(lambda cs=control_surface: control_surface)

def log_memory():
    _connection.root.log_memory()

# def test_adaptor():
#     return _connection.root.test_adaptor_cls()()

def poll():
    if NATIVE:
        client().poll_once()
    else:
        _connection.poll_all()
