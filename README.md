# Hack-Pack-Installer
The installer GUI + background updater for MKW Hack Pack

Windows
  how to compile (This assumes you have the latest version of Python installed and have it in your %PATH%)

  --AUTO-PY-TO-EXE--
    In your command prompt, paste this in and execute: pip install auto-py-to-exe
    Run auto-py-to-exe, and in the interface, fill each box accordingly.
    Check the clear cache setting, and in hidden imports, type: plyer.platforms.win.notification
    Run the program with the above steps completed.

  --INNO SETUP--
    Download Inno Setup from here: https://jrsoftware.org/isdl.php
    Then, after you have gotten Inno Setup installed, run the file "setup.iss" (Be sure to modify as needed) to compile the program into a build script.
    When this is done, simply run the installer to test the program.

NOTE: It is up to the user to try to make this compatible with other OS's, as this was focused on Windows.
