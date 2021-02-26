sudo -i

mkdir data

TRIAL_NO=1
BUCKET_NAME='hippo_data'
TRAIN_DATA_OBJECT='train_test_95-100.pkl'
DATA_LOCATION='/root/data'

gsutil cp gs://$BUCKET_NAME/$TRAIN_DATA_OBJECT $DATA_LOCATION


# Install or update needed software
apt update
apt install -yq git python3 python3-pip
pip3 install --upgrade pip virtualenv

# Account to own server process
# useradd -m -d /home/pythonapp pythonapp

# Fetch source code
# export HOME=/root
git clone https://github.com/jeliason/hippo.git

# Python environment setup
virtualenv -p python3 ~/hippo/scripts/gcp/env
source ~/hippo/scripts/gcp/env/bin/activate

git clone https://github.com/lindermanlab/ssm.git
pip install numpy cython
pip install -e ~/ssm/
# /opt/hippo/scripts/gcp/env/bin/pip install -r /opt/hippo/scripts/gcp/requirements.txt


python /root/hippo/scripts/gcp/slds.py $TRIAL_NO

gsutil cp $DATA_LOCATION/lem_$TRIAL_NO.pkl gs://BUCKET_NAME