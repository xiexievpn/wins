xiexievpn.com


The win client of Xiexie VPN, you can use PyInstaller to make above code into a exe file:

1. Install Python 3 environment, download and install directly from the official website https://www.python.org/downloads/, be sure to check "Add Python to PATH" during installation
   
2. In bash command line as an administrator, switch to the source code directory, then run the following command:
 curl -L -o Xray-windows-64.zip https://github.com/XTLS/Xray-core/releases/download/v25.3.6/Xray-windows-64.zip && tar -xf Xray-windows-64.zip xray.exe geoip.dat geosite.dat && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && pip install pyinstaller && pyinstaller --onefile --noconsole --add-data "favicon.ico;." --add-data "close.bat;." --add-data "internet.bat;." --add-data "xray.exe;." --add-data "geoip.dat;." --add-data "geosite.dat;." --name "xiexievpn" --icon "favicon.ico" main.py && del Xray-windows-64.zip get-pip.py xray.exe geoip.dat geosite.dat
