#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-iisprops

short_description: Set project permissions

version_added: '2.9.13'

description:  Set project permissions for user and/or groups

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''


from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        project=dict(type='str', required=True),
        domain=dict(type='str' ),
        server=dict(type='str',required=True),
        user=dict(type='str',required=True),
        password=dict(type='str',required=True,no_log=True),
        isid=dict(type='str',required=True),
        role=dict(type='str',required=True,choices=['Developer','OperationsViewer','Operator','ProductionManager','SuperOperator']),
        idtype=dict(type='str',default='user',choices=['user','group']),
        absent=dict(type='bool',default=False)
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    import os
    import re
    import subprocess
    result['status'] = 'ok'
    result['changed'] = False
    DS_USER_NAME = module.params['user']
    DS_PASSWORD = module.params['password']
    DS_SERVER = module.params['server']
    DS_PROJECT = module.params['project']
   
    ASBHOME = os.environ['ASBHOME']
    
    result['project'] = DS_PROJECT
    cmdP = [ASBHOME+'/bin/DirectoryCommand.sh','-user',DS_USER_NAME,'-password',DS_PASSWORD]
    if module.params['domain']:
        cmdP = cmdP + ['-url',module.params['domain']]
    else:
        cmdP = cmdP + ['-primary']

    if module.params['absent']:
        action = '-remove_project_'+module.params['idtype']+'_roles'
    else:
        action = '-assign_project_'+module.params['idtype']+'_roles'

    cmd = cmdP +  [action,DS_SERVER+'/'+DS_PROJECT+'$'+module.params['isid']+'$DataStage'+module.params['role']]
    

    result['debug'] = cmd     
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result['output'] = []
    result['remove'] = ''
    result['assign'] = ''
    for line in iter(p.stdout.readline,''):
        result['output'].append(line.strip());
        if re.search("^Error",line):
            module.fail_json(msg=line.strip(), **result)
        if re.search("^Remove",line):
            result['remove'] = re.split('"',re.split('\t',line.strip())[2])[1]
        if re.search("^Project",line):
            result['assign'] = re.split('"',re.split('\t',line.strip())[2])[1]

    p.wait()
    result['status'] = p.returncode
    if p.returncode != 0:
        module.fail_json(msg=result['stdout'],**result)
    if result['assign'] != result['remove']:
        result['changed'] = True


    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
