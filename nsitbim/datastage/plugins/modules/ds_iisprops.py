#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-iisprops

short_description: Set Information Server properties

version_added: '2.9.13'

description:  Set Information Server properties

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''



from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        absent=dict(type='bool',default=False),
        key=dict(type='str',required=True),
        value=dict(type='raw',default='')
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
    import subprocess
    result['status'] = 'ok'
    result['changed'] = False
    update = False
    delete = False
    ROOT = os.environ['IISPath']
    
    cmdP = [ROOT+'/ASBServer/bin/iisAdmin.sh','-display', '-key', module.params['key']]
    result['debug']=cmdP
    current=[]
    p = subprocess.Popen(cmdP, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline,''):
       current.append(line.strip())
    p.wait()
    result['current'] = current
    
    if len(current)>0:
        if module.params['absent']:
            delete = True
        elif current[0].split('=')[1] != module.params['value']:
            update = True 
        else:
            update = False
    else:
        if not module.params['absent']:
           update = True

    if update:
        result['changed'] = True
        cmdP = [ROOT+'/ASBServer/bin/iisAdmin.sh','-set', '-key', module.params['key'], '-value',module.params['value']]
        p = subprocess.Popen(cmdP, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        result['status'] = p.returncode
   
    if delete:
        result['changed'] = True
        cmdP = [ROOT+'/ASBServer/bin/iisAdmin.sh','-unset', '-key', module.params['key']]
        p = subprocess.Popen(cmdP, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        result['status'] = p.returncode



    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
