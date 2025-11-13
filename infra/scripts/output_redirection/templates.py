
"""

TEMPLATES INJECTED EXAMPLES:

- SSH:
      Host bastion
      HostName 44.200.5.230
      User ec2-user
      IdentityFile /Users/javierdominguezsegura/Programming/S25/full-stack/url-shortener/infra/terraform/environment/staging/secrets/ssh_key.pem

      Host staging_web_server
      HostName 10.0.2.226
      User ec2-user
      IdentityFile /Users/javierdominguezsegura/Programming/S25/full-stack/url-shortener/infra/terraform/environment/staging/secrets/ssh_key.pem
      ProxyJump bastion
- Environmental variables:
      KEY:VALUE [map]
- Ansible inventory
      [all:vars]
      ansible_ssh_private_key_file = ./terraform/environment/production/secrets/ssh_key.pem

      [web_servers]
      3.237.195.233 ansible_user=ec2-user

"""
"""
ORGANIZATION PROCESS:
      1. Test in dev with environment only 
"""


ENV_TEMPLATE = """
{% for key, output in outputs.items() %}
{{ key.upper() }}={{ output }}
{% endfor %}
""".strip()



ANSIBLE_TEMPLATE_STAGING = """
[web_servers]
{{ outputs.EC2_APP_SERVER_PRIVATE_IP }} ansible_user={{ outputs.EC2_APP_SERVER_SSH_USER }} ansible_ssh_common_args='-o ProxyCommand"=ssh -i {{ outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH }} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -W %h:%p -q {{ outputs.EC2_BASTION_SERVER_SSH_USER}}@{{ outputs.EC2_BASTION_SERVER_PUBLIC_IP}}"'

[all:vars]
ansible_ssh_private_key_file={{ outputs.EC2_SERVERS_SSH_PRIVATE_KEY_FILE_PATH }} 
"""

ANSIBLE_TEMPLATE_PRODUCTION = """

[web_servers]
{{ outputs.EC2_BASTION_SERVER_PRIVATE_IP }} ansible_user={{ outputs.EC2_APP_SERVER_SSH_USER }}

[all:vars]
ansible_ssh_private_key_file={{ outputs.EC2_APP_SERVER_SSH_PRIVATE_KEY_FILE_PATH }} 


"""