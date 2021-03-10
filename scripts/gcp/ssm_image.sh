#!/bin/bash

# Install or update needed software
apt update
apt install -yq git python3 python3-pip
pip3 install google.cloud google-cloud-storage


git clone https://github.com/lindermanlab/ssm.git
pip3 install numpy cython
pip3 install -e ./ssm/
