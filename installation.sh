# Updating OS
sudo yum update -y
sudo yum upgrade -y
pip3 install --upgrade pip
sudo amazon-linux-extras install epel -y
sudo yum install -y mysql-devel
sudo yum install amazon-cloudwatch-agent -y
export PATH="$PATH:/home/ec2-user/.local/bin"
source ~/.bashrc
mkdir webapp
unzip webapp.zip -d webapp

cd webapp
pip3 install --upgrade pip
python3 -m venv env 
source env/bin/activate 
python3 -m pip install statsd
pip3 install -r requirements.txt    


sudo cp /home/ec2-user/webapp/webapp.service /etc/systemd/system/webapp.service
sudo chown root:root /etc/systemd/system/webapp.service

sudo mv config.json /opt/aws/amazon-cloudwatch-agent/bin/config.json 
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json

#Service file
{
sudo echo [Unit]
sudo echo Description=Python Service
sudo echo After=multi-user.target
sudo echo [Service]

sudo echo Restart=always
sudo echo User=ec2-user
sudo echo Type=simple
sudo echo ExecStart=/home/ec2-user/webapp/env/bin/python3 /home/ec2-user/webapp/main.py
sudo echo WorkingDirectory=/home/ec2-user/webapp/
sudo echo [Install]
sudo echo WantedBy=multi-user.target
} >> webapp1.service

sudo cp /home/ec2-user/webapp/webapp1.service /etc/systemd/system/webapp1.service
sudo chown root:root /etc/systemd/system/webapp1.service
