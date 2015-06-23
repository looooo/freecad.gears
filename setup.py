import sys
import os

from distutils.core import setup

def check_path(path):
    _dir = os.path.dirname(path)
    if not os.path.exists(_dir):
        os.makedirs(_dir)
    return path


def setup_freecad():
    sys.path.append("/usr/lib/freecad/lib")
    try:
        import FreeCAD
    except:
        print("FreeCad is not found!!!")
        return
    fileName = check_path("/usr/lib/freecad/Mod/start_up/InitGui.py")
    try:
        with open(fileName, "r") as startFile:
            lines = startFile.readlines()
            startFile.close()
        start_file_exists = True
    except Exception as e:
        print(e)
        start_file_exists = False
    if start_file_exists:
        for line in lines:
            if "import freecad_gear" in line:
                start_input_exists = True
                break
        else:
            start_input_exists = False
    else:
        start_input_exists = False
    print(fileName)
    if not start_input_exists:
        with open(fileName, "a") as start_file:
            start_file.write("\nimport freecad_gear")

setup(
    name = 'freecad_gear',
    packages = ['freecad_gear'],
    version = '0.1',
    description = 'Some gears for freecad',
    author = 'Lorenz L',
    author_email = 'sppedflyer@gmail.com',
    url = 'https://github.com/looooo/FCGear',
    download_url = 'https://github.com/looooo/FCGear/tarball/0.1',
    keywords = ['gear', 'freecad'],
    classifiers = [],
)

setup_freecad()
