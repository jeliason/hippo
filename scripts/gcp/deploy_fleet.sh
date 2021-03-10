export WEST_ZONE="us-west1-c"
declare -a ZONES=("us-west1-a" "us-west1-b" "us-west1-c" "us-east1-d" "us-east1-b" "us-east1-c" "us-central1-c" "us-central1-a" "us-central1-f" "us-central1-b")
export TEMPLATE="ssm-template"
export TRIALS=$1 # this should be restricted to multiples of MAX_VMS
export STARTUP_SCRIPT="slds_startup.py"
export MAX_VMS=20
export MAX_VMS_PER_ZONE=8

export dt=$(date '+%Y%d%m%H%M%S')

let "TRIALS_PER_VM = ((($TRIALS -1) / $MAX_VMS)+1)"

let "VMS = $TRIALS / $TRIALS_PER_VM"

echo $TRIALS_PER_VM

echo $VMS

for i in `seq 1 $VMS`
do
  let "MIN_IT = ($i - 1) * $TRIALS_PER_VM + 1"
  let "MAX_IT = $i * $TRIALS_PER_VM"
  r=$RANDOM
  for zone in ${ZONES[@]}
    do
      echo $zone
      count=$(gcloud compute instances list  --filter="zone:( $zone )" | grep -o "vm" | wc -l)
      echo $count
      if [[ count -lt $MAX_VMS_PER_ZONE ]]
      then
        gcloud compute instances create "vm-$r" \
        --zone $zone \
        --source-instance-template $TEMPLATE \
        --metadata min_it=$MIN_IT,max_it=$MAX_IT,time=$dt \
        --metadata-from-file startup-script=$STARTUP_SCRIPT
        # --async &
        break
      fi
    done
done
wait