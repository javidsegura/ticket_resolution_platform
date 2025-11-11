

# VPC
resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public_subnet" {
  vpc_id = aws_vpc.main_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "${var.main_region}a"
  map_public_ip_on_launch = true
}
resource "aws_subnet" "private_subnet_a" {
  vpc_id = aws_vpc.main_vpc.id
  cidr_block = "10.0.2.0/24"
  availability_zone = "${var.main_region}a"
  map_public_ip_on_launch = false
}
resource "aws_subnet" "private_subnet_b" {
  vpc_id = aws_vpc.main_vpc.id
  cidr_block = "10.0.3.0/24"
  availability_zone = "${var.main_region}b"
  map_public_ip_on_launch = false
}

resource "aws_internet_gateway" "IGW" {
  vpc_id = aws_vpc.main_vpc.id
}


resource "aws_route_table" "public_IGW_route_table" {
  vpc_id = aws_vpc.main_vpc.id
  route {
      cidr_block = "0.0.0.0/0"
      gateway_id = aws_internet_gateway.IGW.id
  }
}

resource "aws_route_table" "private_subnet_route_table" {
  vpc_id = aws_vpc.main_vpc.id
}

resource "aws_route_table_association" "public_IGW_association" {
  subnet_id = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_IGW_route_table.id
}
resource "aws_route_table_association" "private_association_subnet_b" {
  subnet_id = aws_subnet.private_subnet_a.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}
resource "aws_route_table_association" "private_association_subnet_a" {
  subnet_id = aws_subnet.private_subnet_b.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}
# Subnet Groups
resource "aws_db_subnet_group" "private_subnet_groups" {
  name = "private-subnet-groups"
  subnet_ids = [aws_subnet.private_subnet_a.id, aws_subnet.private_subnet_b.id]
}


# SECURITY GROUPS
resource "aws_security_group" "web_app_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "Public Web App SG"
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress { # For ansible
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database_sg" {
  vpc_id = aws_vpc.main_vpc.id

  name = "Database Security Group"
  ingress {
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    security_groups = [aws_security_group.web_app_sg.id]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
  
}

