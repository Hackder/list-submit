![list-submit](https://github.com/Hackder/list-submit/blob/main/docs/images/list-submit-logo.png)

list-submit is a simple cli utility, that automates submiting problem solutions
to the L.I.S.T. online platform, used by the Faculty of Mathematics and Informatics
Comenius University in Bratislava.

# Installation
*Coming soon*


# Quick start

Run this command to configure your credentials:
```bash
lsbm --auth
```
This command should be run only once, as it will store your credentials in the
global configuration file, located in the installation direcotry, right
next to the list-submit script, named `global-config.toml`.

Go to the directory containing the problem solution and run the list-submit:
```bash
lsbm
```

You will get prompted for the course, and the problem. After answering the questions,
an error will be displayed:
```
No files to submit, the files list is empty.
Add files using the --add flag.
```

*NOTE: Automatic project type detection is comming soon.*

This is because the list-submit utility does not know which files to submit.
You can add files to the list using the `--add` flag:
```bash
lsbm --add *.py
```

Now you can run the list-submit again:
```bash
lsbm
```

At this point everything should be configured and the problem should be submitted
to the L.I.S.T. platform automatically. You should see output similar to this:
```
  Request logging in => done
  Request problems => done      
Submitting solution for <your_problem_name>
  Request submitting solution => done                  
  Request running tests => done
Finished in 0.62 seconds
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
1. Using the `--add`/`--remove` flag
2. Manually editing the `list-submit.toml` file

### Using the `--add`/`--remove` flag:

To add files to the list of files to submit, use the `--add` flag:
```bash
lsbm --add *.py
```
The argument is a glob pattern, that will be expanded to a list of files.
The list will be stored in the `list-submit.toml` file, under the `problem.files` key.

The stored paths will be relative to the directory containing the `list-submit.toml` file,
but you can use this command from any directory from which the config file can be found.

# Projects

List-submit supports the concept of projects. A project is a directory containing
a `list-submit.toml` file. When the list-submit utility is ran with an argument,
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
lsbm project1 # will submit using the configuration in the project1 directory
```

