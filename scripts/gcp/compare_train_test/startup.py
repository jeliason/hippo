#! /usr/bin/python3

import pickle
import ssm
import sys
from google.cloud import storage
import os
from datetime import datetime as dt
import subprocess
import requests
import numpy as np

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

try:              
    time = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/time',
                        headers = {'Metadata-Flavor': 'Google'}).json()

    K = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/K',
                        headers = {'Metadata-Flavor': 'Google'}).json()

    D = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/attributes/D',
                        headers = {'Metadata-Flavor': 'Google'}).json()

    iters = 5
    np.random.seed(K + D)
    DATA_PATH = '/data'
    RESULTS_PATH = DATA_PATH + '/results'
    os.makedirs(RESULTS_PATH, exist_ok=True)

    BUCKET_NAME='hippo_data'
    EXP_NAME = 'compare_train_test/'
    PRE_OBJECT='PRE.pkl'
    RUN_OBJECT='RUN.pkl'
    POST_OBJECT='POST.pkl'

    print('Getting data...')
    download_blob(BUCKET_NAME, EXP_NAME + PRE_OBJECT, DATA_PATH + '/' + PRE_OBJECT)
    download_blob(BUCKET_NAME, EXP_NAME + RUN_OBJECT, DATA_PATH + '/' + RUN_OBJECT)
    download_blob(BUCKET_NAME, EXP_NAME + POST_OBJECT, DATA_PATH + '/' + POST_OBJECT)
    print('Data downloaded')

    binnedPRE = pickle.load(open(DATA_PATH + '/' + PRE_OBJECT, 'rb'))
    binnedRUN = pickle.load(open(DATA_PATH + '/' + RUN_OBJECT, 'rb'))
    binnedPOST = pickle.load(open(DATA_PATH + '/' + POST_OBJECT, 'rb'))

    binnedPRE_1ms = np.concatenate([x[1].T.astype(np.int8) for x in binnedPRE]).astype(int)
    binnedRUN_1ms = np.concatenate([x[1].T.astype(np.int8) for x in binnedRUN]).astype(int)
    binnedPOST_1ms = np.concatenate([x[1].T.astype(np.int8) for x in binnedPOST]).astype(int)

    N = binnedPRE_1ms.shape[1]

    PBEs = {
        'PRE': binnedPRE_1ms,
        'RUN': binnedRUN_1ms,
        'POST': binnedPOST_1ms
    }

    train_test_pairs = [
        {
            'in': ['PRE'],
            'out': ['RUN', 'POST'],
        },
        {
            'in': ['RUN'],
            'out': ['PRE', 'POST'],
        },
        {
            'in': ['POST'],
            'out': ['PRE', 'RUN'],
        },
        {
            'in': ['PRE','POST'],
            'out': ['RUN'],
        }

    ]

    print('Data processed')
    DESTINATION_DATA_PATH = EXP_NAME + f'results/{time}/'

    for pair in train_test_pairs:
        ### training

        print('Starting training on ' + ', '.join(pair['in']))
        y_train = np.concatenate([PBEs[x] for x in pair['in']], axis = 0)
        slds = ssm.SLDS(N, K, D, emissions="poisson_orthog", emission_kwargs=dict(link="softplus"))
        slds.initialize(y_train)

        q_elbos, q = slds.fit(y_train, method="laplace_em",
                                    variational_posterior="structured_meanfield",
                                    num_iters=iters, initialize=False, alpha=0)
        ### testing
        test_results = []
        for test in pair['out']:

            print('Starting testing on ' + test)
            y_test = PBEs[test]
            elbos_test, posterior_test = slds.approximate_posterior(y_test,
                                                    method="laplace_em",
                                                    variational_posterior="structured_meanfield",
                                                    num_iters=iters)
            test_results.append({
                'test_set': test,
                'elbos': elbos_test,
                'posterior': posterior_test
            })
        ### write to file

        print('Writing to file...')
        tr = '-'.join(pair['in'])
        te = '-'.join(pair['out'])
        MODEL_OBJECT = f'K{K}_D{D}_train{tr}_test{te}.pkl'
        pickle.dump([q_elbos, q, slds, test_results], open(RESULTS_PATH + '/' + MODEL_OBJECT, 'wb'))

        upload_blob(BUCKET_NAME, RESULTS_PATH + '/' + MODEL_OBJECT, DESTINATION_DATA_PATH + MODEL_OBJECT)
        print('Uploaded.')       

    print('Finished')
finally:
    cmd = """export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
            export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
            gcloud --quiet compute instances delete $NAME --zone=$ZONE
    """
    subprocess.Popen(cmd, shell=True)