#!/bin/bash

echo "Syncing!"

AWS_SERVERS=('ec2-35-157-212-227.eu-central-1.compute.amazonaws.com' 'ec2-3-123-39-2.eu-central-1.compute.amazonaws.com' 'ec2-3-123-227-107.eu-central-1.compute.amazonaws.com')

for server in "${AWS_SERVERS[@]}";
do
    #ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@$server "sudo apt -qq update && sudo apt -qq install docker-compose -y"
    ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@$server "cd /home/ubuntu && mkdir -p app && cd app && sudo docker-compose down && rm docker-compose.yml"
    echo "Syncing to $server"
    rsync -av --progress -e "ssh -i ~/.ssh/happycucumbers-aws.pem -o StrictHostKeyChecking=no" $PWD/rasa_ai $PWD/server ubuntu@$server:/home/ubuntu/app/
    rsync -av --progress -e "ssh -i ~/.ssh/happycucumbers-aws.pem -o StrictHostKeyChecking=no" $PWD/docker-compose.server.yml ubuntu@$server:/home/ubuntu/app/docker-compose.yml
    ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@$server "cd /home/ubuntu/app && sudo docker-compose up --build -d rasa server"
    echo "Starting docker-compose at $server..."
done


#echo "Syncing to actions server"

#ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@ec2-35-158-103-112.eu-central-1.compute.amazonaws.com "sudo apt -qq update && sudo apt -qq install docker-compose -y"
#ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@ec2-35-158-103-112.eu-central-1.compute.amazonaws.com "cd /home/ubuntu && mkdir -p app && cd app && sudo docker-compose down"
#rsync -av --progress -e "ssh -i ~/.ssh/happycucumbers-aws.pem" $PWD/rasa_ai/actions ubuntu@ec2-35-158-103-112.eu-central-1.compute.amazonaws.com:/home/ubuntu/app/rasa_ai/
#rsync -av --progress -e "ssh -i ~/.ssh/happycucumbers-aws.pem" $PWD/docker-compose.actions.yml ubuntu@ec2-35-158-103-112.eu-central-1.compute.amazonaws.com:/home/ubuntu/app/docker-compose.yml

#ssh -i "~/.ssh/happycucumbers-aws.pem" -o StrictHostKeyChecking=no ubuntu@ec2-35-158-103-112.eu-central-1.compute.amazonaws.com "cd /home/ubuntu/app && sudo docker-compose up --build -d"

#echo "Action server is running!"


echo "Done!"