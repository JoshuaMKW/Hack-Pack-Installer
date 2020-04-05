# Installer Utilities

try:
    import os
    import sys
    import re
    import time
    import platform
    import subprocess
    import shutil
    import psutil
    import winreg as reg

    from plyer import notification
except ImportError:
    sys.exit(1)

def AddToRegistry(file, section, create=True):
    """Add the specified file to be executed on Windows startup"""
    file = os.path.abspath(file)
    print(file, section, create)
      
    # key we want to change is HKEY_CURRENT_USER  
    # key value is Software\Microsoft\Windows\CurrentVersion\Run 
    keytype = reg.HKEY_CURRENT_USER 
    key_value = "Software\Microsoft\Windows\CurrentVersion\Run"
      
    # open the key to make changes to 
    key = reg.OpenKey(keytype, key_value, 0, reg.KEY_ALL_ACCESS) 
      
    # modifiy the opened key
    if create == True:
        reg.SetValueEx(key, section, 0, reg.REG_SZ, file)
    else:
        try:
            reg.DeleteValue(key, section)
        except (WindowsError, OSError):
            pass
      
    # now close the opened key 
    reg.CloseKey(key) 

def is_exe_running(name):
    """Checks if an exe with the given name is active"""
    if name in (p.name() for p in psutil.process_iter()):
        return True
    else:
        return False

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def notify_user(title, message, app=os.path.basename(__file__), icon=None, timeout=10, ticker='', toast=False):
    """If on Windows 7 or above, send a desktop notification to the user"""
    if platform.system() == 'Windows':
        if platform.release() == '7' or platform.release() == '8' or platform.release() == '10':
            notification.notify(title=title, message=message, app_name=app, app_icon=icon, timeout=timeout, ticker=ticker, toast=toast)

def sleepSystem(file, section=None, key=None, flagtype=True, flag='false', timeout=10):
    """Sleeps until flag is set by outside program"""

    start = time.time()
    value = readINI(file, section, key)

    if flagtype == True:
        while value.lower() != flag.lower():
            time.sleep(1)
            curTime = time.time()
            if timeout > 0 and curTime - start > timeout:
                return False
            value = readINI(file, section, key)
    elif flagtype == False:
        while value.lower() == flag.lower():
            curTime = time.time()
            if timeout < 0 or curTime - start > timeout:
                return False
            value = readINI(file, section, key)
    return value

def get_size(start_path = '.'):
    """Get the file size of the input folder"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return format(total_size / 1024 / 1024 / 1024, '.2f')

def disk_usage(file_path):
    usage = shutil.disk_usage(file_path)
    return format(usage.free / 1024 / 1024 / 1024, '.2f')

def get_request_size(URL, byte_size=0):
    """Get the size of the file found in the URL, byte_size = 0:b, 1:kb, 2:mb, 3:gb..."""

    request = requests.get(URL, headers={'User-Agent': 'Custom'}, allow_redirects=True)
    time.sleep(4)
    if 'Content-length' in request.headers:
        if byte_size > 0:
            return format(int(request.headers['Content-length']) / 1024**byte_size, '.2f')
        else:
            return float(request.headers['Content-length'])
    else:
        return None

def cache_settings(autorun, closedsearcher, sleeptime, timelist, timestring, openonupdate, remove, clean, U, P, J, K):
    try:
        writeINI(os.path.abspath('config.ini'), 'Settings', 'autorun', str(autorun.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'closedsearcher', str(closedsearcher.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'openonupdate', str(openonupdate.get()))
        writeINI(os.path.abspath('config.ini'), 'Timings', 'waittimeindex', str(sleeptime.get()))
        writeINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates', str(timelist[timestring.index(sleeptime.get())]))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'remove', str(remove.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'clean', str(clean.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'usa', str(U.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'pal', str(P.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'jap', str(J.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'kor', str(K.get()))
    except FileNotFoundError:
        os.mkdir('bin')
        writeINI(os.path.abspath('config.ini'), 'Settings', 'autorun', str(autorun.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'closedsearcher', str(closedsearcher.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'openonupdate', str(openonupdate.get()))
        writeINI(os.path.abspath('config.ini'), 'Timings', 'waittimeindex', str(sleeptime.get()))
        writeINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates', str(timelist[timestring.index(sleeptime.get())]))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'remove', str(remove.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'clean', str(clean.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'usa', str(U.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'pal', str(P.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'jap', str(J.get()))
        writeINI(os.path.abspath('config.ini'), 'Settings', 'kor', str(K.get()))

def readINI(file, section='', key=''):
    """Read the specified contents of an ini file"""

    regex = re.compile(r'(?<==)(?: *).+')
    found_section = False
    found_key = False

    try:
    
        with open(os.path.abspath(file), 'r') as ini:
            for line in ini.readlines():
                if found_section == False:
                    if re.match(r'(?<!.)\[{}\]'.format(section), line):
                        found_section = True
                else:
                    if re.match(r'(?<!.){}(?= *=)'.format(key), line):
                        value = regex.findall(line)[0]
                        return value.strip()
    except:
        return '0'

def writeINI(file, section='', key='', value=''):
    """Write the specified contents to an ini file"""

    try:
        str(value)
    except:
        raise TypeError('Invalid argument! value was type {}, when it should be int, float, or str.'.format(type(value)))

    try:                
        filecontents = ''
        found_section = False
        found_key = False
        
        with open(os.path.abspath(file), 'r') as ini:
            for line in ini.readlines():
                if found_section == False:
                    if re.match(r'(?<!.)\[{}\]'.format(section), line):
                        found_section = True
                else:
                    if re.match(r'(?<!.){}(?= *=)'.format(key), line):
                        line = re.sub(r'(?<==)(?: *).+', ' ' + value.strip(), line)
                filecontents += line

        with open(file, 'w') as ini:
            ini.write(filecontents)
    except Exception:
        pass

def validate_ini(file, version):
    """Check and create/update config.ini if needed"""

    outdated = False
    version = str(version) + '\n\n'

    if not os.path.isdir(os.path.dirname(file)):
        try:
            os.mkdir(os.path.dirname(file))
        except PermissionError as perm:
            logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(perm))
            sys.exit(1)

    if not os.path.isfile(os.path.basename(file)):
        print('NOT EXIST')
        with open(resource_path('template.ini'), 'r') as template, open(os.path.join(directory, file), 'w') as config:
            config.write(template.read())

    else:
        with open(file, 'r') as config:
            curversion = config.readline().strip()

            regex = re.compile(r'[0-9]+')

            resultNew = regex.findall(version)
            resultCur = regex.findall(curversion)

            try:
                if int(resultNew[0]) > int(resultCur[0]):
                    print('OUTDATED')
                    outdated = True
            except (ValueError, IndexError):
                outdated = True

        if outdated:
            with open(resource_path('template.ini'), 'r') as template, open(file, 'w') as newconfig:
                template.seek(0)
                newconfig.write(version)
                newconfig.write(template.read())
