

# VPC
resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
}


resource "aws_subnet" "public_subnet_bastion_a" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.main_region}a"
  map_public_ip_on_launch = true
}
resource "aws_subnet" "private_subnet_server_a" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.main_region}a"
  map_public_ip_on_launch = false
}
resource "aws_subnet" "private_subnet_data_a" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.3.0/24"
  availability_zone       = "${var.main_region}a"
  map_public_ip_on_launch = false
}
resource "aws_subnet" "private_subnet_data_b" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.4.0/24"
  availability_zone       = "${var.main_region}b"
  map_public_ip_on_launch = false
}


# Route tables
## Public
resource "aws_internet_gateway" "public_IGW" {
  vpc_id = aws_vpc.main_vpc.id
}
resource "aws_route_table" "public_subnet_route_table" {
  vpc_id = aws_vpc.main_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.public_IGW.id
  }
}
resource "aws_route_table_association" "public_association" {
  subnet_id      = aws_subnet.public_subnet_bastion_a.id
  route_table_id = aws_route_table.public_subnet_route_table.id
}

## Private

resource "aws_route_table" "private_subnet_route_table" {
  vpc_id = aws_vpc.main_vpc.id
  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_instance.nat_instance.primary_network_interface_id
  }
}

resource "aws_route_table_association" "private_association_subnet_sever_a" {
  subnet_id      = aws_subnet.private_subnet_server_a.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}
resource "aws_route_table_association" "private_association_subnet_data_a" {
  subnet_id      = aws_subnet.private_subnet_data_a.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}
resource "aws_route_table_association" "private_association_subnet_data_b" {
  subnet_id      = aws_subnet.private_subnet_data_b.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}

# NAT Instance for Private Subnets
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_security_group" "nat_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "NAT Instance SG"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["10.0.0.0/16"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "nat_instance" {
  ami                         = data.aws_ami.amazon_linux_2.id
  instance_type               = "t3.nano"
  subnet_id                   = aws_subnet.public_subnet_bastion_a.id
  associate_public_ip_address = true
  source_dest_check           = false
  vpc_security_group_ids      = [aws_security_group.nat_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sysctl -w net.ipv4.ip_forward=1
              echo net.ipv4.ip_forward = 1 >> /etc/sysctl.conf
              yum install -y iptables-services
              systemctl enable iptables
              systemctl start iptables
              iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
              iptables -F FORWARD
              iptables -A FORWARD -i eth0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
              iptables -A FORWARD -s 10.0.0.0/16 -j ACCEPT
              service iptables save
              EOF

  depends_on = [aws_internet_gateway.public_IGW]

  tags = {
    Name = "NAT instance"
  }
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
}

resource "aws_eip_association" "nat_eip_assoc" {
  allocation_id = aws_eip.nat_eip.id
  instance_id   = aws_instance.nat_instance.id
}

# Subnet Groups
resource "aws_db_subnet_group" "private_subnet_groups" {
  name       = "private-subnet-groups"
  subnet_ids = [aws_subnet.private_subnet_data_a.id, aws_subnet.private_subnet_data_b.id]
}


# SECURITY GROUPS
resource "aws_security_group" "bastion_host_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "Bastion Host SG"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "web_app_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "Private Server SG"
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_host_sg.id]
  }
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_host_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "Database Security Group"
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web_app_sg.id, aws_security_group.bastion_host_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# S3 VPC Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main_vpc.id
  service_name = "com.amazonaws.${var.main_region}.s3"

  route_table_ids = [
    aws_route_table.private_subnet_route_table.id
  ]

  tags = {
    Name = "S3 Gateway Endpoint"
  }
}
