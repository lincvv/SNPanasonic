import os
from cx_Freeze import setup, Executable

__version__ = "1.4b"

os.environ['TCL_LIBRARY'] = "C:\\Python38\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Python38\\tcl\\tk8.6"

include_files = ["img", "data", "uefitool", r"C:\Python38\DLLs\tcl86t.dll", r"C:\Python38\DLLs\tk86t.dll"]
excludes = ['unittest', 'email', 'html', 'http', 'urllib', 'xml', 'pydoc', 'doctest', 'argparse',
            'zipfile', 'pickle', 'locale', 'calendar', 'base64', 'gettext', 'bz2', 'getopt',
            'stringprep', 'quopri', 'copy', 'imp']
packages = ['os', 'binascii', 'mmap', 'subprocess', 'logging', 'webbrowser', 'pathlib', 'time', 'datetime']

setup(
    name="PanasonicTool",
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
