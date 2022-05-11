#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-creds

short_description: Gather project facts

version_added: '2.9.13'

description: Gather properties and project environnement variables

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
    from ansible_collections.nsitbim.datastage.plugins.module_utils.ibm_datastage_api import DSAPI
      
    hproj = None
    dsapi = DSAPI()


    DS_DOMAIN_NAME=''
    DS_USER_NAME=''
    DS_PASSWORD=''
    DS_SERVER=''
    DS_PROJECT = module.params['project']

    res, err = dsapi.DSLoadLibrary(os.environ['DSHOME']+'/lib/libvmdsapi.so')
    dsapi.DSSetServerParams(DS_DOMAIN_NAME, DS_USER_NAME, DS_PASSWORD, DS_SERVER)
    hproj, err = dsapi.DSOpenProject(DS_PROJECT)
    if err:
      module.fail_json(msg="Failed to open the project {}: {}".format(DS_PROJECT,err), **result)
   
    res, err = dsapi.DSListEnvVars(hproj)
    if err:
      module.fail_json(msg="Failed to retrieve environnement variables {}: {}".format(DS_PROJECT,err), **result)
    vars={}
    for var in res:
      vars[var.split('=')[0]]='='.join(var.split('=')[1:])
     
    res, err = dsapi.DSListProjectProperties(hproj)
    if err:
      module.fail_json(msg="Failed to retrieve project properties {}: {}".format(DS_PROJECT,err), **result)
    props={}
    for var in res:
      props[var.split('=')[0]]='='.join(var.split('=')[1:]) 

    res, err = dsapi.DSGetProjectInfo(hproj, dsapi.DSJ_PROJECTPATH)
    if err:
        module.fail_json(msg="Failed to retrieve path {}: {}".format(DS_PROJECT,err), **result)
    path = res

    result['env'] = vars
    result['properties'] = props
    result['project'] = DS_PROJECT
    result['path'] =  path
    
    dsapi.DSCloseProject(hproj)
    hproj = None
    dsapi.DSUnloadLibrary()

    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
