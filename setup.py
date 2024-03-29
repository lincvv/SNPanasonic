import os
from cx_Freeze import setup, Executable

__version__ = "1.5"

os.environ['TCL_LIBRARY'] = "C:\\Python311\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Python311\\tcl\\tk8.6"

include_files = ["img", "data", "uefitool", r"C:\Python311\DLLs\tcl86t.dll", r"C:\Python311\DLLs\tk86t.dll", "fit11"]
excludes = ['unittest', 'email', 'html', 'http', 'xml', 'pydoc', 'doctest', 'argparse',
            'zipfile', 'pickle', 'calendar', 'base64', 'gettext', 'bz2', 'getopt',
            'stringprep', 'quopri', 'copy', 'imp']
packages = ['os', 'binascii', 'mmap', 'subprocess', 'logging', 'webbrowser', 'pathlib', 'time', 'datetime', 'urllib', 'locale']

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
    executables=[Executable("PanasonicTool.py", base="Win32GUI")]
)

# python setup.py bdist_msi
