#!/bin/bash

mkdir data

TRIAL_NO=$(curl http://metadata.google.internal/computeMetadata/v1/instance/attributes/trial -H "Metadata-Flavor: Google")
BUCKET_NAME='hippo_data'
TRAIN_DATA_OBJECT='train_test_95-100.pkl'
DATA_LOCATION=$(readlink -f ./data/)

gsutil cp gs://$BUCKET_NAME/$TRAIN_DATA_OBJECT $DATA_LOCATION


# Fetch source code
# export HOME=/root
git clone https://github.com/jeliason/hippo.git

python3 ./hippo/scripts/gcp/slds.py $TRIAL_NO $DATA_LOCATION

gsutil cp $DATA_LOCATION/lem_$TRIAL_NO.pkl gs://$BUCKET_NAME #TODO

export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
gcloud --quiet compute instances delete $NAME --zone=$ZONE