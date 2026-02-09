#!/bin/bash

set -eu

echo "Extract python312.tar.gz"
sudo rm -rf /opt/python312
sudo tar -xaf python312.tar.gz -C /opt/

sudo /opt/python312/bin/python3 -m pip install --no-index --find-links file:/home/pi/mama/wheels -e .

echo "Install mama application"
sudo chown -R root:root /etc/systemd/system/mama.service
sudo systemctl daemon-reload
sudo systemctl enable mama.service
sudo systemctl start mama.service
sudo systemctl status mama.service
