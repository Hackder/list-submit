# Check Python 3.12 version
$version = (python3 --version).Trim()
if ($version -match "^Python 3\.12.*") {
  Write-Host "Python 3.12 is already installed"
} else {
  Write-Host "Python 3.12 is not installed, please install it first"
  Exit 1
}

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (temporary)
venv\Scripts\Activate.ps1

# Install requirements
python3 -m pip install -r requirements.txt

# Create alias for script execution
New-Alias lsbm -Value "${pwd}\venv\Scripts\python.exe ${pwd}\main.py" -Option Persistent -Scope CurrentUser

