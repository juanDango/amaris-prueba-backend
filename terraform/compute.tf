resource "aws_key_pair" "amaris-key" {
  key_name   = "amaris-key"
  public_key = file("~/.ssh/terraform_rsa.pub")
}

data "archive_file" "app_tgz" {
  type        = "zip"
  source_dir  = "../app"
  output_path = "${path.module}/app.zip"
}

resource "aws_instance" "amaris-webserver" {
  ami                         = "ami-04b70fa74e45c3917"
  associate_public_ip_address = true
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.amaris-subnet-public.id
  vpc_security_group_ids      = [aws_security_group.amaris-public-http-traffic.id]
  root_block_device {
    delete_on_termination = true
    volume_size           = 10
    volume_type           = "gp3"
  }
  key_name = aws_key_pair.amaris-key.key_name

  lifecycle {
    create_before_destroy = true
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("~/.ssh/terraform_rsa")
    host        = self.public_ip
  }


  tags = {
    Name       = "amaris-ec2"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }

  provisioner "file" {
    source      = "${path.module}/app.zip"
    destination = "/home/ubuntu/app.zip"
  }

  # Ejecuta docker build y run
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y docker.io unzip",
      "sudo systemctl enable docker",
      "sudo systemctl start docker",
      "sudo unzip -o /home/ubuntu/app.zip",
      "cd /home/ubuntu",
      "sudo docker build -t fastapi-app .",
      "sudo docker run -d -p 80:8000 fastapi-app",
    ]
  }

}


resource "aws_security_group" "amaris-public-http-traffic" {
  name        = "amaris-public-http-traffic"
  description = "Security group that allows traffic on ports 443 and 80"
  vpc_id      = aws_vpc.amaris-vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic from anywhere"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic from anywhere"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # ⚠️ Esto abre SSH desde cualquier lado
    description = "Allow SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name       = "amaris-sec-group"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}