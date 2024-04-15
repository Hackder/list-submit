#!/bin/bash

version=$(python3 --version)
if [[ $version == "Python 3.12"* ]]; then
  echo "Python 3.12 is already installed"
else
  echo "Python 3.12 is not installed, please install it first"
  exit 1
fi

python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
deactivate
alias lsbm="$(pwd)/venv/bin/python3 $(pwd)/main.py"

echo "An alias lsbm has been created to run the program"
echo "If you want this alias to be permanent, add the following line to your shell configuration file (e.g. ~/.bashrc, ~/.zshrc, etc.):"
echo "alias lsbm=\"$(pwd)/venv/bin/python3 $(pwd)/main.py\""
