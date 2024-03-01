variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "instance_type" {
  type = string
  default= "t2.micro"
}

variable "ssh_username" {
  type    = string
  default = "ec2-user"
}
variable "source_ami" {
  type    = string
  default = "ami-0dfcb1ef8550277af"
}

variable "ami_users" {
    type = list(string)
    default=["864475371348"]
}
variable "subnet_id" {
  type    = string
  default = "subnet-03f710a22535f7224"
}


variable "ami_region" {
  type    = list(string)
  default = ["us-east-1"]
}

source "amazon-ebs" "my-ami" {
  region      = "${var.aws_region}"
  ami_name    = "csye6225_test_ami-${formatdate("YYYY-MM-DD-hhmmss",timestamp())}"
  ami_regions = "${var.ami_region}"
  aws_polling {
    delay_seconds = 120
    max_attempts  = 50
  }
  source_ami_filter {
    filters = {
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["amazon"]
  }
  profile       = "dev"
  instance_type = "${var.instance_type}"
  subnet_id     = "${var.subnet_id}"
  ssh_username  = "${var.ssh_username}"
  ami_users     = "${var.ami_users}"
  source_ami    = "${var.source_ami}"
  launch_block_device_mappings {
    delete_on_termination = true
    device_name           = "/dev/xvda"
    volume_size           = 8
    volume_type           = "gp2"
  }
}
build {

 
  sources = ["amazon-ebs.my-ami"]

  provisioner "file" {
        source = "dist/webapp.zip"
        destination = "/home/ec2-user/webapp.zip"
    }

  provisioner "shell" {
    script = "installation.sh"
  }

  post-processor "manifest" {
   output = "manifest.json"
   strip_path = true
  }
}