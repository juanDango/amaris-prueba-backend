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

  tags = {
    Name       = "amaris-ec2"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
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

  tags = {
    Name       = "amaris-sec-group"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}