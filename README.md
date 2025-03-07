The win client of Xiexie VPN, you can use PyInstaller to make above code into a exe file:

1. Install Python 3 environment, download and install directly from the official website https://www.python.org/downloads/, be sure to check "Add Python to PATH" during installation

2. Download xray.exe: https://github.com/XTLS/Xray-core/releases/tag/v1.8.6 , put it in the source code directory
   
3. In bash command line as an administrator, switch to the source code directory, then run the following command:
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py & python get-pip.py & pip install pyinstaller & pyinstaller --onefile --noconsole --add-data "favicon.ico;." --add-data "createplan.bat;." --add-data "close.bat;." --add-data "internet.bat;." --add-data "xray.exe;." --add-data "geoip.dat;." --add-data "geosite.dat;." --name "xiexievpn" --icon "favicon.ico" main.py

4. there should be a exe file under "source code directory/dist" ,move it to source code directory, then run it.
