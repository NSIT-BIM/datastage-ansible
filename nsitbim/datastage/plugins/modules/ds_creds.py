#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-creds

short_description: Set engine credential mapping

version_added: '2.9.13'

description: Set default, user or group credentials

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''



from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        domain=dict(type='str' ),
        server=dict(type='str',required=True),
        user=dict(type='str',required=True),
        password=dict(type='str',no_log=True,required=True),
        isid=dict(type='str'),
        credUser=dict(type='str',required=True),
        credPassword=dict(type='str',no_log=True),
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
    ASBHOME = os.environ['ASBHOME']

    if module.params['absent']:
        creds='!~!'
    else:
        creds=module.params['credUser']+'~'+module.params['credPassword']
    
    cmdP = [ASBHOME+'/bin/DirectoryCommand.sh','-user',DS_USER_NAME,'-password',DS_PASSWORD,'-datastage_server',module.params['server']]
    if module.params['domain']:
        cmdP = cmdP + ['-url',module.params['domain']]
    else:
        cmdP = cmdP + ['-primary']
    if module.params['isid']:
        action=['-add_ds_credentials',module.params['isid']+'$'+creds]
    else:
        action=['-set_default_ds_credentials', creds]

    cmd = cmdP +  action
    
    result['debug'] = cmd   
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result['output'] = []
    result['set'] = ''
    result['cleared'] = False
    for line in iter(p.stdout.readline,''):
        result['output'].append(line.strip())
        if re.search("^Error",line):
            module.fail_json(msg=line.strip(), **result)
        if re.search(" cleared ",line):
            result['cleared'] = True
        if re.search(" set ",line):
            result['set'] = module.params['credUser'] 

    p.wait()
    result['status'] = p.returncode
    if p.returncode != 0:
        module.fail_json(msg=result['stdout'],**result)
    result['changed'] = True


    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
