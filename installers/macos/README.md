# macOS installer {#macos_installer}

The macOS installer file is the same as the Linux installer file and can be found in the installers/linux folder in the git repo or in the releases folder ( https://github.com/pjaos/retirement_finances/releases ) on github.

## Install

- Ensure you have at least python 3.12 installed.

## Install python on Apple Mac
Details of how to install python on macOS are shown below.

  - Download the installer (at least version 3.12) from https://www.python.org/downloads/macos/

  - Select Downloads Folder in the Dock and click on the above file.

  - Select the Continue, Continue, Continue, Agree and Install buttons.
    You'll be prompted to enter the admin password for the Apple Mac.
    When complete click the Close button.

## Installing pipx
pipx (a python module) is also required. Details of how to install pipx are shown below.

- Open the Launchpad from the Dock.

- Select Other

- Select Terminal

- Run the following commands in the terminal window

```
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

- Close the terminal window.

- Open a new terminal window and enter.

```
pipx --version
1.7.1
```

This verifies that pipx is installed correctly. You may see a later version.

## Installing the retirement finances application

To install the 'Retirements Finances' application open a terminal window in the installers/linux folder or in the location where you downloaded the
retirement_finances-5.0-py3-none-any.whl (version number may change) from https://github.com/pjaos/retirement_finances/releases.

```
pipx install retirement_finances-5.0-py3-none-any.whl
```

```
  installed package retirement-finances 5.0, installed using Python 3.12.3
  These apps are now globally available
    - retirement_finances
done! ✨ 🌟 ✨
```
## Uninstall

To uninstall the retirement finances program enter the terminal below.

```
pipx uninstall retirement_finances
```
