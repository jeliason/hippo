export ZONE="us-west1-c"
export TEMPLATE="ssm-template"
export TRIALS=$1

for i in `seq 1 $TRIALS`
do
  gcloud compute instances create "vm-$i" \
  --zone $ZONE \
  --source-instance-template $TEMPLATE \
  --metadata "trial=$i" \
  --metadata-from-file startup-script=startup_short.sh \
  --async &
done
wait