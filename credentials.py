"""Per-user Windows DPAPI storage. API keys never enter the application ZIP."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
import tempfile

class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def _crypt(data, decrypt=False):
    if sys.platform != 'win32':
        raise OSError('Saving API keys requires Windows credential protection.')
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    output = Blob()
    dll = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    # CRYPTPROTECT_UI_FORBIDDEN: no separate operating-system prompt.
    if decrypt:
        fn = dll.CryptUnprotectData
        fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = (ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    else:
        fn = dll.CryptProtectData
        fn.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = (ctypes.byref(source), 'Purple Dragon GIF Studio GIPHY key', None, None, None, 1, ctypes.byref(output))
    fn.restype = wintypes.BOOL
    if not fn(*args):
        raise OSError('Windows could not protect or unlock the saved API key.')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(ctypes.cast(output.data, ctypes.c_void_p))

class KeyStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'PurpleDragonGIFStudio' / 'giphy-key.dpapi'
    def load(self):
        if not self.path.exists():
            return ''
        return _crypt(self.path.read_bytes(), decrypt=True).decode('utf-8')
    def save(self, key):
        key = key.strip()
        if not key:
            raise ValueError('Enter a GIPHY API key before saving it.')
        protected = _crypt(key.encode('utf-8'))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as file:
                temporary = file.name
                file.write(protected)
            os.replace(temporary, self.path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    def forget(self):
        self.path.unlink(missing_ok=True)
