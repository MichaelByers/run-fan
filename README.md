# run-fan
control a fan for raspberrypi 3b+ based on temperature

Make the script executable.
$ sudo chmod +x run-fan.py

The top comment section has the daemon code,
Paste the contents from the script to the file
$ sudo vi /lib/systemd/system/run-fan.service 

The file must be owned by root and it must be in /lib/systemd/system.
$ sudo chown root:root run-fan.service

After any changes to /lib/systemd/system/run-fan.service:
$ sudo systemctl daemon-reload 
$ sudo systemctl enable run-fan.service 
$ sudo reboot 
