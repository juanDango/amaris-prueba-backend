locals {
  Project    = "amaris-prueba"
  ManagedBy  = "Terraform"
  CostCenter = "1234"
}

resource "aws_vpc" "amaris-vpc" {
  cidr_block = "10.0.0.0/16"

  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name       = "amaris-vpc"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

resource "aws_subnet" "amaris-subnet-public" {
  vpc_id     = aws_vpc.amaris-vpc.id
  cidr_block = "10.0.0.0/24"

  tags = {
    Name       = "amaris-vpc-public"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

resource "aws_internet_gateway" "amaris-igw" {
  vpc_id = aws_vpc.amaris-vpc.id

  tags = {
    Name       = "amaris-igw-public"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

resource "aws_route_table" "amaris-rt-public" {
  vpc_id = aws_vpc.amaris-vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.amaris-igw.id
  }

  tags = {
    Name       = "amaris-rt-public"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

resource "aws_route_table_association" "amaris-rt-public" {
  subnet_id      = aws_subnet.amaris-subnet-public.id
  route_table_id = aws_route_table.amaris-rt-public.id
}
