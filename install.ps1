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

# Install requirements
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Create alias for script execution
Write-Host "To register the alias, add the following line to your PowerShell profile:"
Write-Host "New-Alias lsbm -Value `"${pwd}\venv\Scripts\python.exe ${pwd}\main.py`""

