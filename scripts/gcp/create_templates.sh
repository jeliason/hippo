gcloud compute instances create condor-master-template \
    --zone=us-west1-c \
    --machine-type=n1-standard-1 \
    --image=debian-10-buster-v20210217 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB \
    --metadata-from-file \
         startup-script=condor-master.sh
sleep 300
gcloud compute instances stop \
    --zone=us-west1-c condor-master-template
gcloud compute images create condor-master  \
    --source-disk condor-master-template   \
    --source-disk-zone us-west1-c   \
    --family htcondor-debian
gcloud compute instances delete \
    --quiet \
    --zone=us-west1-c condor-master-template