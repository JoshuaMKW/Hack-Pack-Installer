#! python3

import requests
import shutil
import subprocess
import os
import sys
import re
import time
import configparser
import gspread
import platform
import psutil

from google_drive_downloader import GoogleDriveDownloader as gdd
from oauth2client.service_account import ServiceAccountCredentials
from plyer import notification

import installer_utils as utils

def schedule_check(timer, func, value, args=()):
    """timer equals every x seconds, func = function call, args = arguments"""

    global last_sleep, escape, installing

    while True:
        
        last_time = utils.readINI(os.path.abspath('config.ini'), 'Timings', 'lastsleep')
        if last_time == None:
            continue
        else:
            last_time = time.time() - float(last_time)
        if escape == True:
            return
        start = time.time()
        curTime = (time.time() - start) + last_time
        timer = float(int(utils.readINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates')))
        while curTime < timer:
            while installing == True:
                time.sleep(1)
            if escape == True:
                return
            if timer == 0:
                break
            frequency = time.time()
            if time.time() - frequency < 1:
                time.sleep(1 - (time.time() - frequency))
            curTime = (time.time() - start) + last_time
            timer = float(int(utils.readINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates')))
        
        if timer > 0:
            last_sleep = time.time()
            utils.writeINI(os.path.abspath('config.ini'), 'Timings', 'lastsleep', str(last_sleep))
        
            func[value](*args)

def check_new_update(Scope, CredentialsPath, SheetURL, Page, Notify=True):
    """
        Check if new update is availible

        Scope = Google Sheets Scope
        CredentialsPath = Path to credentials.json file
        SheetURL = Name of Google Spreadsheet
        Page = Name of Page within Spreadsheet
        Notify = Windows notification if new update is available
    """

    print('Checking for update...')
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CredentialsPath, Scope)
    gc = gspread.authorize(credentials)
    
    page = gc.open_by_url(SheetURL).worksheet(Page)
    cells = page.findall(re.compile(r'https://drive\.google\.com/(uc|open)\?id='))

    urls_list = ['downloadurl', 'installerurl']

    for i, cell in enumerate(cells):

        curURL = re.sub(r'open\?id=', 'uc?id=', cell.value)

        p = re.compile(r'(?<=https://drive\.google\.com/uc\?id=)[\w\-]*', flags=re.IGNORECASE)
        
        curURL = p.findall(curURL)[0]
        try:
            oldURL = utils.readINI(os.path.abspath('config.ini'), 'URLS', urls_list[i])
        except IndexError:
            break
        curURL = curURL.strip()
        oldURL = oldURL.strip()
        
        print(curURL)
        print(oldURL)

        installer_status = utils.is_exe_running('Installer.exe')
        
        utils.writeINI(os.path.abspath('config.ini'), 'Timings', 'installerupdateisready', 'false')
        
        if curURL != oldURL:
            if cell.row == 1 and cell.col == 1:
                utils.writeINI(os.path.abspath('config.ini'), 'URLS', 'downloadurl', curURL)
                if Notify and oldURL != '0':
                    utils.notify_user('Update', 'An update for MKW Hack Pack is available!', icon=utils.resource_path(r'hack_pack.ico'), timeout=12600)
                    if int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'openonupdate')) == 1 and installer_status == False:
                        subprocess.Popen('Installer.exe')
                        
            elif cell.row == 2 and cell.col == 1:
                utils.writeINI(os.path.join(appdata, 'config.ini'), 'URLS', 'installerurl', curURL)
                if Notify and oldURL != '0':
                    utils.notify_user('Update', 'An Installer update is available!', icon=utils.resource_path(r'hack_pack.ico'), timeout=12600)
                    if int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'openonupdate')) == 1 and installer_status == False:
                        subprocess.Popen('Installer.exe')
                        
                    utils.writeINI(os.path.abspath('config.ini'), 'Timings', 'installerupdateisready', 'true')

                    status = utils.sleepSystem(os.path.abspath('config.ini'), section='Timings', key='installerupdateisready', flagtype=False, flag='true', timeout=600000)
                    
                    if status == 'active':
                        if os.path.isfile(os.path.join(os.path.expanduser("~"), 'Downloads', 'Installer.zip')):
                            try:
                                os.remove(os.path.join(os.path.expanduser("~"), 'Downloads', 'Installer.zip'))
                            except PermissionError:
                                pass
                        subprocess.run("taskkill /f /im {}".format('Installer.exe'))
                        gdd.download_file_from_google_drive(file_id=curURL, dest_path=os.path.join(os.path.expanduser("~"), 'Downloads', 'Installer.zip'), unzip=True)
                        subprocess.Popen(os.path.join(os.path.expanduser("~"), 'Downloads', 'InstallerSetup.exe'))
                        subprocess.run("taskkill /f /im {}".format(os.path.basename(sys.argv[0])))

if __name__ == '__main__':

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        os.chdir(application_path)

    if os.path.isfile(os.path.join(os.path.expanduser("~"), 'Downloads', 'InstallerSetup.exe')):
        try:
            os.remove(os.path.join(os.path.expanduser("~"), 'Downloads', 'InstallerSetup.exe'))
        except PermissionError:
            pass

    #appdata = os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Programs', 'HackPackInstaller')
    appdata = os.getcwd()

    autorun = int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'autorun'))
    closedsearcher = int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'closedsearcher'))

    with open(os.path.abspath('version.txt'), 'r') as version:
        _version = version.read()
        _version.strip()

    escape = False
    installing = False
    updating = False

    Scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    CredentialsPath = utils.resource_path('credentials.json')
    SheetURL = 'https://docs.google.com/spreadsheets/d/1BBqfrClm8bf-dj5tKT08VGTG-iaely1M-5aZeuChcfY/edit#gid=1676742374'
    Page = 'Private Info'

    utils.validate_ini(os.path.abspath('config.ini'), version=_version)

    '''Run our main update loop'''

    timer = float(int(utils.readINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates')))
    func = {'update' : check_new_update}

    schedule_check(timer, func, 'update', (Scope, CredentialsPath, SheetURL, Page))
