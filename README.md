![list-submit](https://github.com/Hackder/list-submit/blob/main/docs/images/list-submit-logo.png)

list-submit is a simple cli utility, that automates submiting problem solutions
to the L.I.S.T. online platform, used by the Faculty of Mathematics and Informatics at
Comenius University in Bratislava.

# Installation

Copy the provided command to your terminal

## Linux

```bash
wget -q -O /tmp/list-submit-download.tar.gz $(wget -q -O - 'https://api.github.com/repos/Hackder/list-submit/releases/latest' | jq -r '.assets[] | select(.name=="list-submit-x86_64-unknown-linux-gnu.tar.gz").browser_download_url'')
tar -xzf /tmp/list-submit-download.tar.gz -C /tmp
sudo mv /tmp/list-submit /usr/local/bin/lsbm
```

# MacOS aarch64

```bash
wget -q -O /tmp/list-submit-download.tar.gz $(wget -q -O - 'https://api.github.com/repos/Hackder/list-submit/releases/latest' | jq -r '.assets[] | select(.name=="list-submit-aarch64-apple-darwin.tar.gz").browser_download_url'')
tar -xzf /tmp/list-submit-download.tar.gz -C /tmp
sudo mv /tmp/list-submit /usr/local/bin/lsbm
```

## MacOS

```bash
wget -q -O /tmp/list-submit-download.tar.gz $(wget -q -O - 'https://api.github.com/repos/Hackder/list-submit/releases/latest' | jq -r '.assets[] | select(.name=="list-submit-x86_64-apple-darwin.tar.gz").browser_download_url'')
tar -xzf /tmp/list-submit-download.tar.gz -C /tmp
sudo mv /tmp/list-submit /usr/local/bin/lsbm
```

## Windows

```powershell
Invoke-WebRequest -Uri ((Invoke-WebRequest -Uri 'https://api.github.com/repos/Hackder/list-submit/releases/latest' | ConvertFrom-Json).assets | Where-Object { $_.name -eq 'list-submit-x86_64-pc-windows-msvc.zip' }).browser_download_url -OutFile C:\Users\$env:USERNAME\Downloads\list-submit-download.zip
Expand-Archive -Path C:\Users\$env:USERNAME\Downloads\list-submit-download.zip -DestinationPath C:\Users\$env:USERNAME\Downloads\list-submit-download
Move-Item -Path C:\Users\$env:USERNAME\Downloads\list-submit-download\list-submit.exe -Destination C:\Users\$env:USERNAME\AppData\Local\list-submit\lsbm.exe
```

# Quick start

Run this command to configure your credentials:
```bash
lsbm auth
```
This command should be run only once, as it will store your credentials in the
global configuration file, located in `~/.config/list-submit/config.toml` on unix systems
or `C:\Users\<username>\AppData\Roaming\list-submit\config.toml` on Windows.

Go to the directory containing the problem solution and run the list-submit:
```bash
lsbm
```

You will get prompted for the course, and the problem. After answering the questions,
an automatic project detection will run. If it detects everything correctly, all the files
will be added automatically. More on this in [Project Detection](#project-detection)
If not, you will need to add them using the `add` subcommand.
```
lsbm add
```

Now you can run the list-submit again:
```bash
lsbm
```

At this point everything should be configured and the problem should be submitted
to the L.I.S.T. platform automatically. You should see output similar to this:
```
Requesting login => done                                                                                                                               
Requesting submit => done                                                  
Requesting run tests => done
Requesting results => done                                                 
Requesting result => done
```

Done!

# How does it work?

When list-submit is ran, it will look for the `list-submit.toml` file in the current
directory. If no such file is found, it will try again, recursively, in all parent
directories. If no configuration file is found, the utility will ask a few questions
and create the configuration file in the current directory.

List submit also support searching subdirectories for the configuration file.
More on this in the [Projects](#projects) section.

You can modify the contents of this file to change the configuration,
or use any of the available commands.

# Usage

The usage guide assumes that you have set up the `lsbm` alias as described in the
[Installation](#installation) section.

## Adding/removing files to submit

Files can be added in two ways:
1. Using the `add` and `files` subcommands
2. Manually editing the `list-submit.toml` file

### Using the `add` subcommand

To add files to the list of files to submit, use the `add` subcommand:
```bash
lsbm add *.py
```
Valid arguments are:
- **List of files** to add
- **A directory** to add files from. A multiselect prompt will be shown.
- *Nothing* a multiselect prompt will be shown, with the files from the current directory and subdirectories.

The stored paths will be relative to the directory containing the `list-submit.toml` file,
but you can use this command from any directory from which the config file can be found.

# Projects

List-submit supports the concept of projects. A project is a directory containing
a `list-submit.toml` file. When the list-submit utility is ran with the `-p` or `--project` flag,
it will search for the configuration file in any subdirectory named as the provided argument.

Consider the following directory structure:
```
project1/
    list-submit.toml
    solution.py
    tests.py
project2/
    list-submit.toml
    solution.py
    tests.py
```
```bash
lsbm -p project1 # will submit using the configuration in the project1 directory
```

# Project detection
TODO
