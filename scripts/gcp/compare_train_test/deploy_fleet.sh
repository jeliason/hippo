declare -a ZONES=("us-west1-a" "us-west1-b" "us-west1-c" "us-east1-d" "us-east1-b" "us-east1-c" "us-central1-c" "us-central1-a" "us-central1-f" "us-central1-b")
declare -a Ks=(2 3 5 10 15 20 30)
declare -a Ds=(2 3 4 6 8 10)
# declare -a Ks=(2)
# declare -a Ds=(2)
export TEMPLATE="ssm-template"
export STARTUP_SCRIPT="startup.py"
export MAX_VMS_PER_ZONE=8

export dt=$(date '+%Y%d%m%H%M%S')

for K in ${Ks[@]}
do
  echo $K
  for D in ${Ds[@]}
  do
    echo $D
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
          --metadata K=$K,D=$D,time=$dt \
          --metadata-from-file startup-script=$STARTUP_SCRIPT \
          --preemptible \
          --maintenance-policy=terminate
          # --async &
          break
        fi
      done
  done
done
wait