#! /usr/bin/python3

import pickle
import ssm
import sys
from google.cloud import storage
import os
from datetime import datetime as dt
import subprocess
import requests

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)


lb = 95
ub = 100

max_it = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/max_it',
                     headers = {'Metadata-Flavor': 'Google'}).json()

min_it = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/min_it',
                     headers = {'Metadata-Flavor': 'Google'}).json()                    

time = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/time',
                     headers = {'Metadata-Flavor': 'Google'}).json()

DATA_PATH = '/data'
os.mkdir(DATA_PATH)

BUCKET_NAME='hippo_data'
TRAIN_DATA_OBJECT=f'train_test_{lb}-{ub}.pkl'

download_blob(BUCKET_NAME, TRAIN_DATA_OBJECT, DATA_PATH + '/' + TRAIN_DATA_OBJECT)

[y_train, y_test] = pickle.load(open(DATA_PATH + '/' + TRAIN_DATA_OBJECT, 'rb'))
N = y_train.shape[1]
K = 5
D = 2

MODEL_OBJECT = f'N{N}_K{K}_D{D}_it{min_it}-{max_it}.pkl'


DESTINATION_DATA_PATH = f'lem_{lb}-{ub}_{time}'

print("Fitting SLDS with Laplace-EM")

models = []
for i in range(min_it, max_it + 1):

    slds_lem = ssm.SLDS(N, K, D, emissions="poisson_orthog", emission_kwargs=dict(link="softplus"))
    slds_lem.initialize(y_train)

    q_lem_elbos, q_lem = slds_lem.fit(y_train, method="laplace_em",
                                variational_posterior="structured_meanfield",
                                num_iters=20, initialize=False, alpha=0)
    models.append([q_lem_elbos, q_lem, slds_lem])

pickle.dump(models, open(DATA_PATH + '/' + MODEL_OBJECT, 'wb'))

upload_blob(BUCKET_NAME, DATA_PATH + '/' + MODEL_OBJECT, DESTINATION_DATA_PATH + '/' + MODEL_OBJECT)

cmd = """export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
        export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
        gcloud --quiet compute instances delete $NAME --zone=$ZONE
"""
subprocess.Popen(cmd, shell=True)