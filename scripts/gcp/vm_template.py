"""Creates a Compute Engine Instance."""

script = '''mkdir data

            TRIAL_NO=$(curl http://metadata.google.internal/computeMetadata/v1/instance/attributes/trial -H "Metadata-Flavor: Google")
            BUCKET_NAME='hippo_data'
            TRAIN_DATA_OBJECT='train_test_95-100.pkl'
            DATA_LOCATION=$(readlink -f ./data/)

            gsutil cp gs://$BUCKET_NAME/$TRAIN_DATA_OBJECT $DATA_LOCATION


            # Fetch source code
            # export HOME=/root
            git clone https://github.com/jeliason/hippo.git

            python3 ./hippo/scripts/gcp/slds.py $TRIAL_NO $DATA_LOCATION

            gsutil cp $DATA_LOCATION/lem_$TRIAL_NO.pkl gs://$BUCKET_NAME

            export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
            export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
            gcloud --quiet compute instances delete $NAME --zone=$ZONE'''

def get_script():
    with open('startup_short.sh', "r") as text_file:
        script = text_file.read()
    return script

def GenerateConfig(context):
  """Generate configuration."""

  resources = []
  for i in range(context.properties['trials']):
    resources.append({
      'name': 'vm-' + str(i),
      'type': 'compute.v1.instance',
      'properties': {
          'zone': 'us-west1-c',
          'machineType': 'zones/us-west1-c/machineTypes/e2-medium',
          'disks': [{
              'deviceName': 'boot',
              'type': 'PERSISTENT',
              'boot': True,
              'autoDelete': True,
              'initializeParams': {
                  'sourceImage':
                      'projects/comp-neuro-304717/global/machineImages/ssm'
              }
          }],
          'metadata': {
              'items': [{
                  'key':'startup-script',
                  'value': script
              },
              {
                  'key':'trial',
                  'value': i
              }]
          }
      }
  })

  return {'resources': resources}
