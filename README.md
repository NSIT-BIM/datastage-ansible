
# Ansible for DataStage

Collection to automate IBM Information Server DataStage administration.


## Installation

Install the collection with the ansible galaxy cli:

```bash
ansible-galaxy collection install git+https://github.com/NSIT-BIM/datastage-ansible.git#nsitbim
```
    
## Features

### Roles

#### common
This role sets up the necessary variables and facts. It should be called first in most playbooks.

#### ds_project_admin
This role is for project level administration:
* Project provisioning/deletion
* Properties
* Environment variables
* User/group permissions
* ODBC Connections
* Parellism configuration

#### ds_server_admin
This role is for environment level administration:
* IIS properties
* Engine credentials
* OBDC configuration
* Engine configuration
* ODBC Connections
* Services handling

### Modules
The tasks could all call various DataStage commands but to reduce complexity in tasks definition new modules are used:
* **ds-creds**: Engine credentials
* **ds-env**: Set project environment variables
* **ds-facts**: Gather project properties and variables
* **ds-iisprops**: Set IIS properties
* **ds-ini**: Gather ini file information
* **ds-perms**: Set project permissions
* **ds-project**: Create/delete project
* **ds-props**: Set project properties



## Usage

Ansible allows a vast ways of usage. Here we would recommend using playbooks:
* One for the environment administration
* One by project

And use inventory files with group_vars for each environment (development, production...).

Run the playbooks for the prod inventory:

````bash
 ansible-playbook environment.yml -i prod
````
````bash
 ansible-playbook project.yml -i prod
````

Tags can be specified to run only specific tasks: config, perms, debug, apt, uvconfig, odbc, creds, env

## Demo

### Setup
#### Inventory
In the provided example the environment is `demo` as declared in the inventory file where we declare all the hosts tiers for the environment.

````ini name=test
[demo:children]
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

#### group variables

In the file `group_vars/demo/vars` we define environment specific variables. All can be overriden when needed.
`````yaml
---
env: demo
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
In the file `group_vars/demo/vault` we define secrets. This file is intended to be [encrypted](https://docs.ansible.com/ansible/latest/user_guide/vault.html). This file should not be commited in any repository.
`````yaml
isadminPassword: isadmin
dsadmPassword: dsadmin
pgPassword: pgpassword
`````

### Environment playbook

In this file we define the environnment level configuration.
````yaml
# file : ds.yml
# description: example playbook for iis administration

---
# these first variables are mandatory
# engine is defined in the inventory file but hosts could be hard coded or reference a variable
- hosts: engine
  remote_user: root
  environment:
          IISPath: /opt/IBM/InformationServer

  roles:
      - nsitbim.datastage.common
      - nsitbim.datastage.ds_server_admin
  vars:
        # set default and users credentials for the engine.
        credentials:
            default:
               user: "{{ dsadm }}"
               password: "{{ dsadmPassword }}"
            users:
                 - name: developer
                   user: dsadm
                   password: "{{ dsadmPassword }}"
        #uvconfig properties
        uvconfig:
            MFILES: 200
        

        # odbc connections definitions
        # connections are defined in the group_vars
        odbc:
          postgresDb:
            label: "Postgres DataBase" 
            configuration:
             - Driver: /opt/IBM/InformationServer/Server/branded_odbc/lib/VMpsql00.so
             - Description: DataDirect 7.0 PostgreSQL Wire Protocol
             - Database: "{{ databases.postgres.db }}"
             - HostName: "{{ databases.postgres.host }}"
             - PortNumber: "{{ databases.postgres.port }}"
             - QueryTimeout: 30

````

### Project playbook

In this file we define the project configuration
````yaml
# file : project.yml
# description: example playbook for project administration

---
# these first variables are mandatory
# engine is defined in the inventory file but hosts could be hard coded or reference a variable
- hosts: engine
  remote_user: dsadm
  roles:
      - nsitbim.datastage.common
      - nsitbim.datastage.ds_project_admin
  vars:
        # project name
        project: dstage3

        # set project level permissions
        permissions:
                users: 
                   developer:
                     role: Developer 
                  
        # parallelism configuration
        nodes: 3
        apt_config_file: "apt_config_file.{{ nodes }}nodes.apt"

        # odbc connections
        odbc: [ postgresDb ]

        # project properties 
        # they are defined by labels
        properties:
                Handle Failed Activities: true
                Log Warnings: true
                Log Report: true
                Supress Summary: false
                Generate Operational Metadata: false
                RCP For New Links: true
                OSH Visible: true
                Job Administration: true
                RCP: true
                Protected: false
                Purges:
                        Days: 15

        # project environnement variables
        ds_env:
                - name: example_var
                  value: "example_val"
                  prompt: "this is an example"
                - name: pg_password
                  value: "{{ databases.postgres.password }}"
                  prompt: "database password"
                  encrypted: true
                - name: pg_user
                  value: "{{ databases.postgres.user }}"
                  prompt: "database user"
                - name: pg_host
                  value: "{{ databases.postgres.host }}"
                  prompt: "database host"
                - name: APT_CONFIG_FILE
                  value: "{{ APT_CONFIG_FILE }}"


````


## Acknowledgements

Several tasks rely on the python implementation of the DataStage API by [@reijnn](https://github.com/reijnnn):
[IBM-DataStage-API](https://github.com/reijnnn/IBM-DataStage-API) big thanks for his work.