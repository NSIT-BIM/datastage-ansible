# Ansible for DataStage

Collection of modules and roles to automate IBM Information Server DataStage administration.

# Dependencies

Several tasks rely on the python implementation of the DataStage API by [@reijnn](https://github.com/reijnnn):
[IBM-DataStage-API](https://github.com/reijnnn/IBM-DataStage-API) big thanks for his work.

The library beeing stable it was directly included in this repository as is to simplify the installation.

# Roles

## common
This role sets up the necessary variables and facts. It should be called first in most playbooks.

## ds_project_admin
This role is for project level administration:
* Project provisioning/deletion
* Properties
* Environment variables
* User/group permissions
* ODBC Connections
* Parellism configuration

## ds_server_admin
This role is for environment level administration:
* IIS properties
* Engine credentials
* OBDC configuration
* Engine configuration
* ODBC Connections
* Services handling

# Modules
The tasks could all call various DataStage commands but to reduce complexity in tasks definition new modules are used:
* **ds-creds**: Engine credentials
* **ds-env**: Set project environment variables
* **ds-facts**: Gather project properties and variables
* **ds-iisprops**: Set IIS properties
* **ds-ini**: Gather ini file information
* **ds-perms**: Set project permissions
* **ds-project**: Create/delete project
* **ds-props**: Set project properties

# Usage
Ansible allows a vast ways of usage. Here we would recommend using playbooks:
* One for the environment administration
* One by project

And use inventory files with group_vars for each environment (development, production...).

See the provided example.

# Example
## Setup
### Inventory
In the provided example the environment is `tst` as declared in the inventory file where we declare all the hosts tiers for the environment.

````ini
[tst:children]
engine
domain
xmeta

[engine]
engine_hostname

[domain]
services_hostname port=9446 

[xmeta]
repository_hostname
````

### group variables

In the file `group_vars/tst/vars` we define environment specific variables. All can be overriden when needed.
`````yaml
---
env: tst
user: isadmin
password: "{{isadminPassword}}"
dsadm: dsadm
# DataSets and scratch location
datasets: /opt/IBM/InformationServer/Server/Datasets
scratch: /opt/IBM/InformationServer/Server/Scratch
# DataSets and scratch project specific location
# datasets: /opt/IBM/InformationServer/Server/Datasets/{{project}}
# scratch: /opt/IBM/InformationServer/Server/Scratch/{{project}}

# Set default permissions
permissions:
      groups:
           developerGroup:
              role: Developer

# We can define our DataBase connections here
db:
  postgres:
      host: pg_host
      user: pguser
      password: "{{pgPassword}}"
      port: 5432
`````
In the file `group_vars/tst/vault` we define secrets. This file is intended to be [encrypted](https://docs.ansible.com/ansible/latest/user_guide/vault.html). This file should not be commited in any repository.
`````yaml
isadminPassword: isadmin
dsadmPassword: dsadmin
pgPassword: pgpassword
`````

### Environment playbook

In this file we define the environnment level configuration.
````yaml
- hosts: engine
  remote_user: root
  environment:
          # IIS Installation path
          IISPath: /opt/IBM/InformationServer
  roles:
      - common
      - ds_server_admin
  vars:
        # default credentials for the engine.
        credentials:
            default:
               user: "{{ dsadm }}"
               password: "{{ dsadmPassword }}"
            users:
                 - name: developerUser
                   user: dsadm
                   password: "{{ dsadmPassword }}"

        # uvconfig properties
        uvconfig:
            MFILES: 200
        
        # odbc connections definitions
        odbc:
           - name: postgres
             type: PostgreSQL Wire Protocol
             label: test pg
             configuration:
                 HostName: "{{ db.postgres.host }}"
                 DataBase: postgres
                 PortNumber: "{{ db.postgres.port }}"

````

### Project playbook

In this file we define the project configuration
````yaml
- hosts: engine
  remote_user: dsadm
  roles:
          - common
          - ds_project_admin

  vars:
        # project name
        project: dstage1
        permissions:
                users: 
                   developerUser:
                     role: Developer 
        # parallelism configuration
        nodes: 2
        apt_config_file: "{{ project }}.apt"
        # odbc connections
        odbc: [ postgres ]
        # project properties 
        # they are defined by labels (see configuration.properties in roles/ds_project_admin/defaults/main.yml)
        properties:
                Handle Failed Activities: true
                Log Warnings: true
                Log Report: false
                Supress Summary: false
                Generate Operational Metadata: false
                RCP For New Links: true
                OSH Visible: true
                Job Administration: true
                RCP: true
                Protected: false
                Advanced Runtime Options: 
                Purges:
                        #Days: 15
                        Runs: 5

        # project environnement variables
        ds_env:
                - name: example_var
                  value: "example_val"
                  prompt: "this is an example"
                - name: pg_password
                  value: "{{ db.postgres.password }}"
                  prompt: "database password"
                - name: pg_user
                  value: "{{ db.postgres.user }}"
                  prompt: "database user"
                - name: pg_host
                  value: "{{ db.postgres.host }}"
                  prompt: "database host"
                - name: APT_CONFIG_FILE
                  value: "{{ APT_CONFIG_FILE }}"

````

## Run playbooks

Run the playbooks for the tst inventory:

````bash
 ansible-playbook ds.yml -i tst
````
````bash
 ansible-playbook project.yml -i tst
````

Tags can be specified to run only specific tasks: config, perms, debug, apt, uvconfig, odbc, creds, env