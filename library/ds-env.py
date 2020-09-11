#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-env

short_description: Project environnement variables configuration

version_added: '2.9.13'

description: Add, update, delete project environnement variables

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''



from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        project=dict(type='str', required=True),
        domain=dict(type='str'),
        server=dict(type='str'),
        user=dict(type='str'),
        password=dict(type='str',no_log=True),
        variable=dict(type='str',required=True),
        value=dict(type='str',default=''),
        encrypted=dict(type='bool',default=False),
        prompt=dict(type='str'),
        absent=dict(type='bool',default=False),
        env=dict(type='dict',default=())
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
    from ansible.module_utils.ibm_datastage_api import DSAPI
      
    hproj = None
    dsapi = DSAPI()


    DS_DOMAIN_NAME=''
    DS_USER_NAME=''
    DS_PASSWORD=''
    DS_SERVER=''
    DS_PROJECT = module.params['project']
    DS_VARIABLE = module.params['variable']
    DS_VALUE = module.params['value'] 
    DS_PROMPT = DS_VARIABLE
    DS_TYPE = dsapi.DSA_ENVVAR_TYPE_STRING
    if module.params['encrypted']:
        DS_TYPE = dsapi.DSA_ENVVAR_TYPE_ENCRYPTED
    if module.params['prompt']:
        DS_PROMPT = module.params['prompt']
    if module.params['domain']:
        DS_DOMAIN_NAME = module.params['domain']
    if module.params['user']:
        DS_USER_NAME = module.params['user']
    if module.params['password']:
        DS_PASSWORD = module.params['password']
    if module.params['server']:
        DS_SERVER = module.params['server']

    res, err = dsapi.DSLoadLibrary(os.environ['DSHOME']+'/lib/libvmdsapi.so')
    dsapi.DSSetServerParams(DS_DOMAIN_NAME, DS_USER_NAME, DS_PASSWORD, DS_SERVER)
    hproj, err = dsapi.DSOpenProject(DS_PROJECT)
    if err:
      module.fail_json(msg="Failed to open the project {}: {}".format(DS_PROJECT,err), **result)
  
    if len(module.params['env']) == 0:
       res, err = dsapi.DSListEnvVars(hproj)
       if err:
         module.fail_json(msg="Failed to retrieve environnement variables {}: {}".format(DS_PROJECT,err), **result)
       vars={}
       for var in res:
         vars[var.split('=')[0]]='='.join(var.split('=')[1:])
    else:
        vars = module.params['env']
    
    create = False
    update = False
    delete = False
    result['skipped'] = False
    result['status'] = 'ok'
    result['variable'] = DS_VARIABLE
    if DS_VARIABLE in vars:
        wasEncrypted = False
        if vars[DS_VARIABLE] != DS_VALUE:
            update = True
        if re.match("\{iisenc\}",vars[DS_VARIABLE]):
            wasEncrypted = True
        if module.params['absent']:
            delete = True
            update = False
        if wasEncrypted and not module.params['encrypted']:
            delete = True
            create = True
        if not wasEncrypted and module.params['encrypted']:
            delete = True
            create = True
    else:
        create = True
        if module.params['absent']:
            create = False
    if delete:
        res, err = dsapi.DSDeleteEnvVar(hproj,DS_VARIABLE)
        if err:
           module.fail_json(msg="Failed to delete {}:{}".format(DS_VARIABLE,err), **result)
        result['changed'] = True
        result['skipped'] = False
        result['status'] = 'deleted'
    if create:
        res, err = dsapi.DSAddEnvVar(hproj,DS_VARIABLE,DS_TYPE,DS_PROMPT,DS_VALUE)
        if err:
           module.fail_json(msg="Failed to add {}:{}".format(DS_VARIABLE,err), **result)
        result['changed'] = True
        result['skipped'] = False
        result['status'] = 'created'
    if update:
        res,err = dsapi.DSSetEnvVar(hproj,DS_VARIABLE,DS_VALUE)
        if err:
           module.fail_json(msg="Failed to set {}:{}".format(DS_VARIABLE,err), **result)
        result['changed'] = True
        result['skipped'] = False
        result['status'] = 'updated'

    dsapi.DSCloseProject(hproj)
    hproj = None
    dsapi.DSUnloadLibrary()
    result['project'] = DS_PROJECT
  
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
