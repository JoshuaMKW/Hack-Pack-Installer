#! python3

try:
    import requests
    import shutil
    import tkinter
    import os
    import sys
    import re
    import time
    import platform
    import logging
    import threading
    import gspread
    import configparser
    import subprocess
    import webbrowser
    import winsound

    from tkinter import *
    from tkinter import ttk, filedialog, messagebox
    from google_drive_downloader import GoogleDriveDownloader as gdd
    from oauth2client.service_account import ServiceAccountCredentials
    from plyer import notification
    from bs4 import BeautifulSoup as Soup
    from PIL import Image, ImageTk

    import installer_utils as utils
except ImportError as err:
    print(err)
    time.sleep(4)
    sys.exit(1)

class TextScrollCombo(ttk.Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    # ensure a consistent GUI size
        self.grid_propagate(False)
    # implement stretchability
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # create a Text widget
        self.txt = Text(self)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    # create a Scrollbar and associate it with txt
        scrollb = ttk.Scrollbar(self, command=self.txt.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set

def raise_frame(frame, button, tabs=[], istabbed=False):
    frame.tkraise()
    if istabbed:
        for tab in tabs:
            if tab['text'] == button['text']:
                button.config(relief=FLAT)
                button.config(state=DISABLED)
            else:
                tab.config(relief=RAISED)
                tab.config(state=NORMAL)

def show_info(title, message):
    tkinter.messagebox.showinfo(title, message)

def check_update_flags():

    global last_sleep, escape, installing

    timer = 1

    while True:
        if escape == True:
            return
        start = time.time()
        curTime = time.time() - start
        while curTime < timer:
            while installing == True:
                time.sleep(1)
            if escape == True:
                return
            curTime = time.time() - start

        installer_ready = utils.readINI(os.path.join(appdata, 'config.ini'), 'Timings', 'installerupdateisready')
        
        if installer_ready == 'true':
            install = messagebox.askyesno('Update', 'An installer update is available!\nWould you like to proceed with the installation?\n\n(The installer will automatically exit while it updates)')
            if install:
                utils.writeINI(os.path.abspath('config.ini'), 'Timings', 'installerupdateisready', 'active')
                while True:
                    time.sleep(10)
            else:
                utils.writeINI(os.path.abspath('config.ini'), 'Timings', 'installerupdateisready', 'false')

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

        p = re.compile(r'(?<=https://drive\.google\.com/uc\?id=)\w*', flags=re.IGNORECASE)
        
        curURL = p.findall(curURL)[0]
        oldURL = utils.readINI(os.path.abspath('config.ini'), 'URLS', urls_list[i])
        
        print(curURL)
        print(oldURL)
        
        if curURL != oldURL:
            if Notify:
                if cell.row == 1 and cell.col == 1:
                    utils.notify_user('Update', 'An update for MKW Hack Pack is available!', icon=utils.resource_path(r'hack_pack.ico'), timeout=12600)
                elif cell.row == 2 and cell.col == 1:
                    utils.notify_user('Update', 'An Installer update is available!', icon=utils.resource_path(r'hack_pack.ico'), timeout=12600)
                    update_installer = messagebox.yesno('Update', 'Install the lastest update of the MKW Hack Pack installer?')
                    if update_installer:

                        global updating
                        updating = True
                        
                        on_closing()
                        
                utils.writeINI(os.path.abspath('config.ini'), 'URLS', urls_list[i], curURL)

def on_closing(bypass=False):
    global installing, last_sleep

    query = None

    if not bypass:
        if installing == False:
            query = messagebox.askokcancel("Exiting", "Do you want to exit?")
        else:
            query = messagebox.askokcancel("Exiting", "Are you sure you want to abort the install and exit?")

    if query or bypass:

        try:
            utils.cache_settings(autorun, closedsearcher, sleeptime, timelist, timestring, openonupdate, remove, clean, U, P, J, K)
            if autorun.get() == 1:
                utils.AddToRegistry('Installer.exe', 'MKWHP_Installer')
            else:
                utils.AddToRegistry('Installer.exe', 'MKWHP_Installer', create=False)
        except Exception as err:
            logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(err))
            
        global escape
        escape = True

        if not bypass:
        
            root.quit()
            root.destroy()
            
            tupdate.join()

        try:
            shutil.rmtree('tmp')
        except (PermissionError, FileNotFoundError):
            pass
        if closedsearcher.get() == 0:
            subprocess.run("taskkill /f /im {}".format('Updater.exe'))
        subprocess.run("taskkill /f /im {}".format(os.path.basename(sys.argv[0])))

def remove_files(file_path):
    for folder in os.listdir(file_path):
        if re.search(r'hack[\s_]*pack', folder, flags=re.IGNORECASE):
            hack_pack = os.path.join(file_path, folder)
            if os.path.isdir(hack_pack):
                try:
                    shutil.rmtree(hack_pack)
                except (PermissionError, FileNotFoundError):
                    print('Failed to remove {}. Try checking if the folder is open somewhere'.format(hack_pack))
        elif re.search(r'riivolution', folder, flags=re.IGNORECASE):
            for file in os.listdir(os.path.join(file_path, "riivolution")):
                if re.search(r'hack[\s_]*pack[\s_]*.*.xml', file, flags=re.IGNORECASE):
                    file = os.path.join(file_path, "riivolution", file)
                    try:
                        os.remove(file)
                    except (PermissionError, FileNotFoundError):
                        print('Failed to remove {}. Try checking if the file is open somewhere'.format(file))

def clean_misplaced(file_path):
    for root, dirs, files in os.walk(file_path, topdown=True):
        for name in dirs:
            path = os.path.join(root, name)
            folder = (os.path.basename(os.path.normpath(path)))
            if re.search(r'hack(| |_)pack|riivolution|apps', folder, flags=re.IGNORECASE) and re.search(r'[hH]ack(| |_)[pP]ack|riivolution|apps', root, flags=re.IGNORECASE):
                if folder != 'riivolution':
                    shutil.rmtree(path)
                    print('Cleaned misplaced {} folder from the installation'.format(path))
                elif not 'apps' in path:
                    shutil.rmtree(path)
                    print('Cleaned misplaced {} folder from the installation'.format(path))


def check_install():
    file_path = filedialog.askdirectory(title='Select the Root of an SD Card or USB Drive', parent=root, mustexist=True)
    if re.match(r'[a-bA-Bd-zD-Z]:/(?![\w\s])', file_path):
        tbar = threading.Thread(target=cleaning_tools, args=(file_path, remove, clean))
        tbar.daemon = True
        tbar.start()
        progress_bar()
        tbar.join()
    elif file_path == '':
        return
    else:
        tkinter.messagebox.showwarning('Invalid Path', "The Installer only accepts the root of an external drive, please try again!")

def cleaning_tools(file_path, remove, clean):
    if remove.get() == 1:
        print("Remove flag initiated")
        remove_files(file_path)
    if clean.get() == 1:
        print("Clean flag initiated")
        clean_misplaced(file_path)
    install(file_path)

def progress_bar():

    global ft

    def install_closing():
        if messagebox.askokcancel("Cancel", "Are you sure you want to cancel the install?"):
            ft.grab_release()
            ft.destroy()

    button_1['text'] = 'Installing, this will take a while...'
    button_1['relief'] = 'flat'

    ft = Toplevel(root)
    ft.geometry('240x30')
    ft.title('Installing')
    ft.transient(root)
    ft.grab_set()

    ft.wm_protocol("WM_DELETE_WINDOW", on_closing)
    ft.iconbitmap(utils.resource_path('hack_pack.ico'))
    ft.resizable(0, 0)

    pb_hD = ttk.Progressbar(ft, orient='horizontal', mode='indeterminate')
    pb_hD.pack(fill=BOTH, expand=True)
    pb_hD.start(20)

def install(file_path):

    global installing

    curURL = utils.readINI(os.path.join(appdata, 'config.ini'), 'URLS', 'downloadurl')
    
    GB = float(utils.disk_usage(file_path))
    if remove.get() == 1:
        for folder in os.listdir(file_path):
            if os.path.isdir(os.path.join(file_path, folder)) and re.search(r'[hH]ack(| |_)[pP]ack', folder, flags=re.IGNORECASE):
                previous_pack = float(utils.get_size(os.path.join(file_path, folder)))
                GB = GB + previous_pack

    final_size = 1.2
            
    if U.get() == 0:
        final_size = final_size - 0.045
    if P.get() == 0:
        final_size = final_size - 0.045
    if J.get() == 0:
        final_size = final_size - 0.045
    if K.get() == 0:
        final_size = final_size - 0.045
    elif U.get() == 0 and P.get() == 0 and J.get() == 0 and K.get() == 0:
        final_size = 1.2

    for package in packageList:
        final_size = final_size + packageList[package][2]
    
    print('{:0.2f}'.format(GB), "GB Free Space")
    print('{:0.2f}'.format(final_size), "GB needed")
    print(packageList[package][1], packageList[package][1].get())
    if GB < final_size:
        ft.destroy()
        button_1['text'] = 'Install'
        button_1['relief'] = 'raised'
        tkinter.messagebox.showwarning("Insufficient Space", """There is not enough space on your drive! MKW Hack Pack needs at least {:0.2f}GB of space for the install of the regions for the chosen packs!
You currently have {:0.2f}GB of space on your drive!""".format(final_size, GB))
        return

    installing = True
    error = False
    original_directory = os.getcwd()
    try:
        os.chdir(os.path.join(os.getcwd(), 'tmp'))
        
        gdd.download_file_from_google_drive(file_id=curURL, dest_path=os.path.join(os.getcwd(), 'MKW Hack Pack.zip'), unzip=True, overwrite=True)

        for package in packageList:
            print(packageList[package][1], packageList[package][1].get())
            if packageList[package][1].get() == 1:
                gdd.download_file_from_google_drive(file_id=packageList[package][0], dest_path=os.path.join(os.getcwd(), package + '.zip'), unzip=True, overwrite=True)

        status = False
        if U.get() == 1 or P.get() == 1 or J.get() == 1 or K.get() == 1:
            status = clear_unwanted_regions(file_path, U, P, J, K)

        for file in os.listdir(os.path.join(os.getcwd(), 'riivolution')):
            if not os.path.isdir(os.path.join(file_path, 'riivolution')):
                os.mkdir(os.path.join(file_path, 'riivolution'))
                time.sleep(1)
            shutil.copyfile(os.path.join(os.getcwd(), 'riivolution', file), os.path.join(file_path, 'riivolution', file))
        for folder in os.listdir():
            if re.search(r'[hH]ack(| |_)[pP]ack', folder, flags=re.IGNORECASE) and os.path.isdir(os.path.join(os.getcwd(), folder)):
                shutil.copytree(os.path.join(os.getcwd(), folder), os.path.join(file_path, folder), dirs_exist_ok=True)
        os.chdir(original_directory)

        for file in os.listdir('tmp'):
            file_path = os.path.join('tmp', file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete {}. Reason: {}'.format(file_path, e))

        utils.notify_user('Hack Pack Installer', 'Install complete! Thank you for choosing MKW Hack Pack!', icon=utils.resource_path(r'hack_pack.ico'), timeout=3600)
        button_1['text'] = 'Install'
        button_1['relief'] = 'raised'
        installing = False
        ft.destroy()
        if status == True:
            tkinter.messagebox.showinfo("Info", "Install complete! Thank you for choosing MKW Hack Pack!")
        else:
            tkinter.messagebox.showerror("Error", "Install completed, but the installer failed to filter the regions!")
        
    except Exception as err:
        logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(err))
        print(err)
        os.chdir(original_directory)

        for file in os.listdir('tmp'):
            file_path = os.path.join('tmp', file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete {}. Reason: {}'.format(file_path, e))
                
        installing = False
        ft.destroy()
        button_1['text'] = 'Install'
        button_1['relief'] = 'raised'
        tkinter.messagebox.showerror("Error", "Install failed. Check your drive and internet connection, and try again.")
        return

def clear_unwanted_regions(file_path, U, P, J, K):
    """Args must be of type IntVar(), Returns True if successful"""
    try:
        for folder in os.listdir():
            if os.path.isdir(os.path.join(os.getcwd(), folder)):
                if re.search(r'[hH]ack(| |_)[pP]ack', folder, flags=re.IGNORECASE):
                    for root, dirs, files in os.walk(os.path.join(os.getcwd(), folder), topdown=True):
                        for subfolder in dirs:
                            if U.get() == 0:
                                if re.search(r'(?<![\w\s-])(USA|US|U|NTSC-U)(?![\w\s-])', subfolder, flags=re.IGNORECASE):
                                    shutil.rmtree(os.path.join(root, subfolder))
                            if P.get() == 0:
                                if re.search(r'(?<![\w\s-])(PAL|PL|P)(?![\w\s-])', subfolder, flags=re.IGNORECASE):
                                    shutil.rmtree(os.path.join(root, subfolder))
                            if J.get() == 0:
                                if re.search(r'(?<![\w\s-])(JAP|JP|J|NTSC-J)(?![\w\s-])', subfolder, flags=re.IGNORECASE):
                                    shutil.rmtree(os.path.join(root, subfolder))
                            if K.get() == 0:
                                if re.search(r'(?<![\w\s-])(KOR|KR|K|NTSC-K)(?![\w\s-])', subfolder, flags=re.IGNORECASE):
                                    shutil.rmtree(os.path.join(root, subfolder))
                                    
                elif folder == 'riivolution':                
                    for file in os.listdir(os.path.join(os.getcwd(), folder)):
                        if os.path.splitext(file.lower()) == '.xml':
                            if U.get() == 0:
                                if re.search(r'(USA|US|U|NTSC-U)', file, flags=re.IGNORECASE):
                                    os.remove(os.path.join(os.getcwd(), folder, file))
                            if P.get() == 0:
                                if re.search(r'(PAL|PL|P)', file, flags=re.IGNORECASE):
                                    os.remove(os.path.join(os.getcwd(), folder, file))
                            if J.get() == 0:
                                if re.search(r'(JAP|JP|J|NTSC-J)', file, flags=re.IGNORECASE):
                                    os.remove(os.path.join(os.getcwd(), folder, file))
                            if K.get() == 0:
                                if re.search(r'(KOR|KR|K|NTSC-K)', file, flags=re.IGNORECASE):
                                    os.remove(os.path.join(os.getcwd(), folder, file))
                        
        return True
    except Exception as err:
        return False

def spawn_settings():

    def save_settings():
        try:
            utils.cache_settings(autorun, closedsearcher, sleeptime, timelist, timestring, openonupdate, remove, clean, U, P, J, K)
            if autorun.get() == 1:
                utils.AddToRegistry('Installer.exe', 'MKWHP_Installer')
            else:
                utils.AddToRegistry('Installer.exe', 'MKWHP_Installer', create=False)
        except Exception as err:
            logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(err))
            try:
                if os.path.isdir('tmp'):
                    shutil.rmtree('tmp')
            except (PermissionError, FileNotFoundError):
                pass
            
        spawn.grab_release()
        spawn.destroy()
        
    spawn = Toplevel(root)
    spawn.transient(root)
    spawn.title('Settings')

    

    windowWidth = 400
    windowHeight = 300
    positionRight = int(root.winfo_screenwidth()/2 - windowWidth/2)
    positionDown = int(root.winfo_screenheight()/3.3 - windowHeight/2)
    
    spawn.geometry('+{}+{}'.format(positionRight, positionDown))
    spawn.grab_set()

    spawn.wm_protocol("WM_DELETE_WINDOW", save_settings)
    
    spawn.iconbitmap(utils.resource_path('hack_pack.ico'))
    
    spawn.resizable(0, 0)

    pre_frame = Frame(spawn, padx=4, relief=GROOVE, borderwidth=2)
    pre_frame.grid(sticky=N+S+E+W, row=0, column=0)

    Checkbutton(pre_frame, variable=remove, text="Remove Previous Installs").grid(sticky=W, row=1, column=0, padx=6, pady=2)
    Checkbutton(pre_frame, variable=clean, text="Clean Offending Files").grid(sticky=W, row=2, column=0, padx=6, pady=1)

    region_frame = Frame(spawn, padx=4, relief=GROOVE, borderwidth=2)
    region_frame.grid(sticky=N+S+E+W, row=0, column=1)
    
    Checkbutton(region_frame, variable=U, text='America').grid(sticky=W, row=1, column=0, padx=3, pady=2)
    Checkbutton(region_frame, variable=P, text='Europe').grid(sticky=W, row=1, column=1, padx=3, pady=2)
    Checkbutton(region_frame, variable=J, text='Japan').grid(sticky=W, row=2, column=0, padx=3, pady=1)
    Checkbutton(region_frame, variable=K, text='Korea', state=DISABLED).grid(sticky=W, row=2, column=1, padx=3, pady=1)

    update_frame = Frame(spawn, padx=4, pady=2, relief=GROOVE, borderwidth=2)
    update_frame.grid(sticky=N+S+E+W, row=1, column=0, columnspan=2)

    misc_frame1 = Frame(spawn, padx=4, pady=2, relief=GROOVE, borderwidth=2)
    misc_frame1.grid(sticky=N+S+E+W, row=2, column=0, columnspan=2)
    misc_frame1.columnconfigure(1, weight=1)

    Label(update_frame, text='Auto Search Updates:').grid(padx=28, pady=5)

    sleep = OptionMenu(update_frame, sleeptime, *timestring)
    sleep.grid(row=0, column=1, pady=2)

    Checkbutton(misc_frame1, variable=closedsearcher, text='Background Updates').grid(sticky=W, row=1, column=0, padx=6, pady=2)
    Checkbutton(misc_frame1, variable=autorun, text='Auto Run on Login').grid(sticky=W, row=2, column=0, padx=6, pady=2)
    Checkbutton(misc_frame1, variable=openonupdate, text='Open GUI on Update').grid(sticky=W, row=3, column=0, padx=6, pady=2)

    BEEEEP = Button(misc_frame1, relief=FLAT, command=lambda:winsound.PlaySound('telephone.wav', winsound.SND_FILENAME|winsound.SND_NOWAIT))
    BEEEEP.grid(sticky=N+S+E+W, row=1, column=1, rowspan=3, padx=6, pady=2)

def main_buttons(mainframe):

    global button_1, menu

    def thread_install():
        tcheck = threading.Thread(target=check_install, args=())
        tcheck.daemon = True
        tcheck.start()

    menu = Menu(root)
    root.config(menu = menu)
    subm = Menu(menu, tearoff=False)
    sub1 = Menu(menu, tearoff=False)
    sub2 = Menu(menu, tearoff=False)
    menu.add_cascade(label="Settings", command=spawn_settings)
    
    menu.add_cascade(label="Help", menu=sub1)
    
    sub1.add_command(label="Clean Misplaced Files", command=lambda:show_info("Help", """When activated, 'Clean Misplaced Files' searches
the install directory for previous installs of MKW Hack Pack
that are located in the wrong directory of the
destination drive, and removes them accordingly."""))
    
    sub1.add_command(label="Remove Previous Installs", command=lambda:show_info("Help", """When activated, 'Remove Previous Installs' automatically
deletes any previous install of MKW Hack Pack
before the current install proceeds.

This is highly recommended as it can keep issues from occuring due to conflicting files."""))
    
    sub1.add_command(label="Regions", command=lambda:show_info("Help", """This determines which regions of MKW Hack Pack are installed.

This is useful for when you don't have a lot of drive space.
Leaving all regions unchecked causes all regions to be installed."""))
    
    sub1.add_command(label="Auto Search Updates", command=lambda:show_info("Help", """This determines how often the installer will
automatically search for new updates.
If it finds a new version exists, it alerts
the user that an update is available."""))

    sub1.add_command(label="Background Updates", command=lambda:show_info("Help", """'Background Updates' determines if the updater
should continue running even if the GUI is terminated."""))

    sub1.add_command(label="Auto Run on Login", command=lambda:show_info("Help", """If checked, 'Auto Run on Login' will make
installer auto open everytime you login to Windows.
Note that unchecking it will make it not open
on Windows login."""))

    sub1.add_command(label="Open GUI on Update", command=lambda:show_info("Help", """Only works when Background Updates is enabled,
'Open GUI on Update' makes the updater
open the main Installer GUI when
an update is available for download."""))
    
    sub1.add_command(label="Install", command=lambda:show_info("Help", """Downloading MKW Hack Pack vX is a mandatory process.
Checking the boxes in the panel adds additional downloads.

Clicking 'Install' will cause a prompt for a directory to be set.
Please set the directory to the root of your SD card for the install to work properly.

Install times vary between 5 to 30 minutes depending on the
amount of things being installed, as well as
download speeds, and drive speeds.

No user input is needed after the install. Simply put the SD card into your Wii and play!"""))
    
    menu.add_command(label="About", command=lambda:show_info("About", "Packs developed by: Huili, JoshuaMK\nInstaller developed by: JoshuaMK"))

    '''ALL THINGS INSTALL'''

    packagesFrame = Frame(mainframe, relief=GROOVE, borderwidth=2)
    packagesFrame.grid(sticky=N+S+E+W, row=0, column=0)
    
    installFrame = Frame(mainframe)
    installFrame.grid(sticky=N+S+E+W, row=1, column=0)

    '''Get packages'''

    print(packageList)
    for package in packageList:
        packageList[package][1] = IntVar(0)
        check = Checkbutton(packagesFrame, text=package, variable=packageList[package][1])
        check.pack(side=TOP, fill=BOTH, expand=1)

    button_1 = Button(installFrame, text="Install!", font=('Helvetica', 20), command=thread_install)
    button_1.pack(side=BOTTOM, fill=BOTH, expand=True)
    
if __name__ == '__main__':

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        os.chdir(application_path)

    with open(os.path.abspath('version.txt'), 'r') as version:
        _version = version.read()
        _version.strip()

    try:
        escape = False
        installing = False
        updating = False

        Scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        CredentialsPath = utils.resource_path('credentials.json')
        SheetURL = 'https://docs.google.com/spreadsheets/d/1BBqfrClm8bf-dj5tKT08VGTG-iaely1M-5aZeuChcfY/edit#gid=1676742374'
        Page = 'Private Info'

        credentials = ServiceAccountCredentials.from_json_keyfile_name(CredentialsPath, Scope)
        gc = gspread.authorize(credentials)
    
        page = gc.open_by_url(SheetURL).worksheet(Page)

        i = 5
        package = page.cell(i, 1).value
        packageList = {}

        while package:
            packagesplit = package.split(';')
            try:
                packagesplit[0] = packagesplit[0].strip()
            except (IndexError, TypeError):
                tkinter.messagebox.showerror("Fatal Error", "Name is invalid or unprovided. Please contact Huili with this issue if it persists")
                break
            try:
                packagesplit[1] = packagesplit[1].strip()
            except (IndexError, TypeError):
                tkinter.messagebox.showerror("Fatal Error", "Package URL invalid is unprovided. Please contact Huili with this issue if it persists")
                break
            try:
                packagesplit[2] = float(packagesplit[2].strip())
            except (IndexError, TypeError):
                packagesplit[2] = float(0)
            
            packagesplit[1] = re.sub(r'open\?id=', 'uc?id=', packagesplit[1])
            p = re.compile(r'(?<=https://drive\.google\.com/uc\?id=)[\w\-]*', flags=re.IGNORECASE)
            packagesplit[1] = p.findall(packagesplit[1])[0]
            print(packagesplit)
            packageList[packagesplit[0]] = [packagesplit[1], 0, packagesplit[2]]

            i += 1
            package = page.cell(i, 1).value

        changelog = page.cell(3, 1).value

        thiccfont = ('Helvetica', 12)

        main_site = 'https://mkwhackpack.com/'
        wiiki = 'http://wiki.tockdom.com/wiki/MKW_Hack_Pack'
        discord = 'https://discord.gg/bERSEbx'
        youtube = 'https://www.youtube.com/user/HuiliGouPJ'
        twitch = 'https://www.twitch.tv/huiligou'

        #appdata = os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Programs', 'HackPackInstaller')
        appdata = os.getcwd()

        utils.validate_ini(os.path.abspath('config.ini'), version=_version) 

        '''Run our main update loop'''

        timer = float(int(utils.readINI(os.path.abspath('config.ini'), 'Timings', 'searchupdates')))

        func = {'update' : check_new_update}

        root=Tk()
        root.withdraw()
        root.after(0, root.deiconify)
        
        windowWidth = 500
        windowHeight = 500

        # Gets both half the screen width/height and window width/height.
        positionRight = int(root.winfo_screenwidth()/2 - windowWidth/2)
        positionDown = int(root.winfo_screenheight()/3 - windowHeight/2)


        root.title("Hack Pack Installer")
        if windowWidth > 0 and windowHeight > 0:
            root.geometry('{}x{}+{}+{}'.format(windowWidth, windowHeight, positionRight, positionDown)) #290x180
        else:
            root.geometry('+{}+{}'.format(positionRight, positionDown))
        root.iconbitmap(utils.resource_path('hack_pack.ico'))
        root.resizable(0, 0)

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        tabsframe = Frame(root)
        tabsframe.grid(sticky=N+E+W, row=0, column=0)
        tabsframe.columnconfigure(0, weight=1)

        '''
        wiimmfiframe = Frame(root)
        wiimmfiframe.grid(sticky=N+S+E+W, row=1, column=0)
        wiimmfiframe.columnconfigure(0, weight=1)
        wiimmfiframe.rowconfigure(0, weight=1)
        '''

        '''
        Label(wiimmfiframe, text="This hasn't been\nimplemented yet!", font=('Helvetica', 30)).grid(sticky=N+S+E+W)
        '''

        """Make info buttons that take you to websites"""

        updateframe = Frame(root)
        updateframe.grid(sticky=N+S+E+W, row=1, column=0)
        updateframe.columnconfigure(0, weight=1)
        updateframe.rowconfigure(1, weight=1)

        Label(updateframe, text='-Change Log-', font=thiccfont, relief=GROOVE, borderwidth=2).grid(sticky=N+S+E+W, row=0, column=0)

        changelogframe = TextScrollCombo(updateframe)
        changelogframe.grid(sticky=N+S+E+W, row=1, column=0)
        changelogframe.txt.tag_configure("center", justify='center')
        changelogframe.txt.insert(INSERT, changelog)
        changelogframe.txt.tag_add("center", "1.0", "end")
        changelogframe.txt.configure(state=DISABLED)
        changelogframe.txt.bind("<1>", lambda event: changelogframe.focus_set())

        websiteframe = Frame(updateframe)
        websiteframe.grid(sticky=N+S+E+W, row=2, column=0)

        img_hpbanner = Image.open(utils.resource_path('hack_pack.ico'))
        img_yt = Image.open(utils.resource_path('youtube.png'))
        img_tw = Image.open(utils.resource_path('twitch.png'))
        img_wiiki = Image.open(utils.resource_path('wiiki.png'))
        img_dc = Image.open(utils.resource_path('discord.png'))
        
        hp_banner = ImageTk.PhotoImage(img_hpbanner)
        hp_youtube = ImageTk.PhotoImage(img_yt)
        hp_twitch = ImageTk.PhotoImage(img_tw)
        hp_wiiki = ImageTk.PhotoImage(img_wiiki)
        hp_discord = ImageTk.PhotoImage(img_dc)

        Label(websiteframe, text='-MKW Hack Pack Media-', font=thiccfont, relief=GROOVE, borderwidth=2).pack(side=TOP, fill=BOTH, expand=True)

        main_link = Button(websiteframe, text='Website', image=hp_banner, relief=GROOVE, borderwidth=2, compound='top', command=lambda:webbrowser.open(main_site))
        main_link.pack(side=LEFT, fill=BOTH, expand=1)
        #main_link.columnconfigure(0, weight=1)

        wiiki_link = Button(websiteframe, text='Wiiki', image=hp_wiiki, relief=GROOVE, borderwidth=2, compound='top', command=lambda:webbrowser.open(wiiki))
        wiiki_link.pack(side=LEFT, fill=BOTH, expand=1)
        #main_link.columnconfigure(1, weight=1)

        youtube_link = Button(websiteframe, text='YouTube', image=hp_youtube, relief=GROOVE, borderwidth=2, compound='top', command=lambda:webbrowser.open(youtube))
        youtube_link.pack(side=LEFT, fill=BOTH, expand=1)
        #main_link.columnconfigure(0, weight=1)

        twitch_link = Button(websiteframe, text='Twitch', image=hp_twitch, relief=GROOVE, borderwidth=2, compound='top', command=lambda:webbrowser.open(twitch))
        twitch_link.pack(side=LEFT, fill=BOTH, expand=1)
        #main_link.columnconfigure(1, weight=1)

        discord_link = Button(websiteframe, text='Discord', image=hp_discord, relief=GROOVE, borderwidth=2, compound='top', command=lambda:webbrowser.open(discord))
        discord_link.pack(side=LEFT, fill=BOTH, expand=1)
        #main_link.columnconfigure(0, weight=1)

        """Do the tabs and main page"""

        mainframe = Frame(root)
        mainframe.grid(sticky=N+S+E+W, row=1, column=0, rowspan=3)
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        
        tabs = []

        installs = Button(tabsframe, text='Installs', width=18, pady=3, disabledforeground='black', relief=FLAT, state=DISABLED, command=lambda:raise_frame(mainframe, installs, tabs=tabs, istabbed=True))
        tabs.append(installs)
        websites = Button(tabsframe, text='Info', width=18, pady=3, disabledforeground='black', command=lambda:raise_frame(updateframe, websites, tabs=tabs, istabbed=True))
        tabs.append(websites)
        '''
        wiimmfi = Button(tabsframe, text='Wiimmfi', width=18, pady=3, disabledforeground='black', command=lambda:raise_frame(wiimmfiframe, wiimmfi, tabs=tabs, istabbed=True))
        tabs.append(wiimmfi)
        '''

        for i, tab in enumerate(tabs):
            tab.pack(side=LEFT, fill=X, expand=1)
            #tab.columnconfigure(0, weight=1)
            #tab.rowconfigure(0, weight=1)

        U = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'usa')))
        P = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'pal')))
        J = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'jap')))
        K = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'kor')))
        clean = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'clean')))
        remove = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'remove')))
        sleeptime = StringVar(value=utils.readINI(os.path.abspath('config.ini'), 'Timings', 'waittimeindex'))
        closedsearcher = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'closedsearcher')))
        autorun = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'autorun')))
        openonupdate = IntVar(value=int(utils.readINI(os.path.abspath('config.ini'), 'Settings', 'openonupdate')))

        if not utils.is_exe_running('Updater.exe'):
            subprocess.Popen('Updater.exe')

        tupdate = threading.Thread(target=check_update_flags, args=())
        tupdate.daemon = True
        tupdate.start()

        ft = ''
        t1 = ''

        timestring = ['Every Minute',
                      'Every 10 Minutes',
                      'Every 30 Minutes',
                      'Every Hour',
                      'Every 6 Hours',
                      'Every Day',
                      'Every Week',
                      'Every Month',
                      'Never']

        timelist = [60,
                    600,
                    1800,
                    3600,
                    21600,
                    86400,
                    604800,
                    2630880,
                    0]

        try:
            if os.path.isdir('tmp'):
                shutil.rmtree('tmp')
                while os.path.isdir('tmp'):
                    time.sleep(1)
            os.mkdir('tmp')
        except PermissionError as perm:
            logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(err))
            tkinter.messagebox.showerror('Permission Error', perm)
            try:
                shutil.rmtree('tmp')
            except (PermissionError, FileNotFoundError):
                pass
            if closedsearcher.get() == 0:
                subprocess.run("taskkill /f /im {}".format('Updater.exe'))
            subprocess.run("taskkill /f /im {}".format(os.path.basename(sys.argv[0])))
            sys.exit(1)
        temporary_dir = os.path.join(os.getcwd(), 'tmp')
        
        try:
            logging.basicConfig(filename='ERROR.txt', filemode='a', level=logging.ERROR, format='\n%(asctime)s\n')
            logger=logging.getLogger(__name__)
            
            item = IntVar()
            backmodel = IntVar()
            timerpos = IntVar()
            minimap = IntVar()
            character = IntVar()

            tbuttons = threading.Thread(target=main_buttons, args=(mainframe,))
            tbuttons.daemon = True
            tbuttons.start()

            root.mainloop()

        except Exception as err:
            logger.exception('-'*len('::FATAL ERROR::') + '\n::FATAL ERROR::\n' + '-'*len('::FATAL ERROR::') + '\n' + str(err))
            try:
                shutil.rmtree('tmp')
            except (PermissionError, FileNotFoundError):
                pass
            if closedsearcher.get() == 0:
                subprocess.run("taskkill /f /im {}".format('Updater.exe'))
            subprocess.run("taskkill /f /im {}".format(os.path.basename(sys.argv[0])))
            sys.exit(1)
    except KeyboardInterrupt:
        try:
            shutil.rmtree('tmp')
        except (PermissionError, FileNotFoundError):
            pass
        if closedsearcher.get() == 0:
            subprocess.run("taskkill /f /im {}".format('Updater.exe'))
        subprocess.run("taskkill /f /im {}".format(os.path.basename(sys.argv[0])))
