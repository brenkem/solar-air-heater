# solar-air-heater
heater used to use solar excess electricity


## enable service via systemd
    cp solar-air-heater.service /lib/systemd/system
    systemctl daemon-reload
    systemctl enable solar-air-heater.service
