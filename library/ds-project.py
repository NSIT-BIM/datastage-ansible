#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-iisprops

short_description: create/delete project

version_added: '2.9.13'

description:  create/delete project

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''


from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        project=dict(type='str', required=True),
        domain=dict(type='str',default=''),
        server=dict(type='str',default=''),
        user=dict(type='str',default=''),
        password=dict(type='str',default='',no_log=True),
        path=dict(type='str',default=''),
        absent=dict(type='bool',default=False), 
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
    from ansible.module_utils.ibm_datastage_api import DSAPI
      
    hproj = None
    dsapi = DSAPI()
    delete = False
    create = False
    result['status'] = 'ok'
    result['changed'] = False
    DS_DOMAIN_NAME = module.params['domain']
    DS_USER_NAME = module.params['user']
    DS_PASSWORD = module.params['password']
    DS_SERVER = module.params['server']
    DS_PROJECT = module.params['project']
    DS_LOCATION = module.params['path']

    res, err = dsapi.DSLoadLibrary(os.environ['DSHOME']+'/lib/libvmdsapi.so')
    dsapi.DSSetServerParams(DS_DOMAIN_NAME, DS_USER_NAME, DS_PASSWORD, DS_SERVER)
   
    res, err = dsapi.DSGetProjectList()
    if err:
      module.fail_json(msg="Cant't get projects list : {}".format(err), **result)
    
    if DS_PROJECT in res:
      if module.params['absent']:
        delete = True
      else:
        create = False 
    else :
       if module.params['absent']:
         delete = False
       else:
         create = True
   
    if delete:
       res, err = dsapi.DSDeleteProject(DS_PROJECT)
       if err:
          module.fail_json(msg="Failed to delete the project {}: {}".format(DS_PROJECT,err), **result)
       else:
          result['changed'] = True
          result['status'] = 'deleted'
     
    if create:
        res, err = dsapi.DSAddProject(DS_PROJECT,DS_LOCATION) 
        if err:
          module.fail_json(msg="Failed to create the project {}: {}".format(DS_PROJECT,err), **result)
        else:
          result['changed'] = True
          result['status'] = 'created'         
 
 
    result['project'] = DS_PROJECT
    
    dsapi.DSCloseProject(hproj)
    hproj = None
    dsapi.DSUnloadLibrary()

    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
