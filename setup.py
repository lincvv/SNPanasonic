import os
from cx_Freeze import setup, Executable

__version__ = "1.1"

os.environ['TCL_LIBRARY'] = "C:\\Python36\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Python36\\tcl\\tk8.6"

include_files = ['img', r"C:\Python36\DLLs\tcl86t.dll", r"C:\Python36\DLLs\tk86t.dll"]
excludes = ['logging', 'unittest', 'email', 'html', 'http', 'urllib',
            'xml', 'pydoc', 'doctest', 'argparse', 'datetime', 'zipfile',
            'subprocess', 'pickle', 'threading', 'locale', 'calendar',
            'tokenize', 'base64', 'gettext', 'bz2', 'getopt', 'stringprep',
            'contextlib', 'quopri', 'copy', 'imp']
packages = ["os", "binascii", "mmap"]

setup(
    name="SNPanasonic",
    description='App Description',
    version=__version__,
    options={"build_exe": {
        'packages': packages,
        'include_files': include_files,
        'excludes': excludes,
        'include_msvcr': True,
    }},
    executables=[Executable("app.py", base="Win32GUI")]
)

# python setup.py bdist_msi
