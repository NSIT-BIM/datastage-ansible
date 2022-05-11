#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-iisprops

short_description: Set project properties

version_added: '2.9.13'

description:  Set project properties

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
        dsproperty=dict(type='str',required=True),
        value=dict(type='raw', required=True),
        props=dict(type='dict',default=())
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
    propertiesMap=dict(
      OSHVisible='OSHVisibleFlag',
      JobAdminEnabled='JobAdminEnabled',
      RTCPEnabled='RTCPEnabled',
      ProtectedMode='ProtectionEnabled',
      PXAdvRTOptions='PXAdvRTOptions',
      PXDeployCustomAction='PXDeployCustomAction',
      PXDeployJobDirectoryTemplate='PXDeployJobDirectoryTemplate',
      PXRemoteBaseDirectory='PXRemoteBaseDirectory',
      PXDeployGenerateXML='PXDeployGenerateXML',
      PurgeEnabled='PurgeEnabled',
    )
    defaultResMap = { False: '0', True:'1', 'False': '0', 'True': '1', 'false': '0', 'true': '1' }
    resultsMap=dict(
      OSHVisible=defaultResMap,
      JobAdminEnabled=defaultResMap,
      RTCPEnabled=defaultResMap,
      ProtectedMode=defaultResMap,
      PXDeployGenerateXML=defaultResMap
    )
    propertiesLabels=dict()
    propertiesLabels['OSH Visible']='OSHVisible'
    propertiesLabels['Job Administration']='JobAdminEnabled'
    propertiesLabels['RCP']='RTCPEnabled'
    propertiesLabels['Protected']='ProtectedMode'
    propertiesLabels['Advanced Runtime Options']='PXAdvRTOptions'
    propertiesLabels['Deploy Custom Action']='PXDeployCustomAction'
    propertiesLabels['Deploy Directory Template']='PXDeployJobDirectoryTemplate'
    propertiesLabels['Remote Base Directory']='PXRemoteBaseDirectory'
    propertiesLabels['Deploy Generate XML']='PXDeployGenerateXML'
    propertiesLabels['Purges']='PurgeEnabled'
    DS_DOMAIN_NAME=''
    DS_USER_NAME=''
    DS_PASSWORD=''
    DS_SERVER=''
    DS_PROJECT = module.params['project']
    DS_PROPERTY = module.params['dsproperty']
    DS_VALUE = module.params['value']
    if module.params['domain']:
        DS_DOMAIN_NAME = module.params['domain']
    if module.params['user']:
        DS_USER_NAME = module.params['user']
    if module.params['password']:
        DS_PASSWORD = module.params['password']
    if module.params['server']:
        DS_SERVER = module.params['server']
    
    if DS_PROPERTY == 'Purges': 
        if type(DS_VALUE) is dict:
           if 'Days' in DS_VALUE and 'Runs' in DS_VALUE:
              module.warn('Days/Runs => Only one attribute will be used') 
           if not ('Days' in DS_VALUE or 'Runs' in DS_VALUE):
               module.fail_json(msg='For Purges property at least Days or Runs must be specified')
           if 'Days' in DS_VALUE:
              _DS_VALUE = 'TRUE -days '+str(DS_VALUE['Days'])
              DS_VALUE = _DS_VALUE
           if 'Runs' in DS_VALUE:
              _DS_VALUE = 'TRUE -runs '+str(DS_VALUE['Runs'])
              DS_VALUE = _DS_VALUE
        else:
            DS_VALUE = 'FALSE'

    res, err = dsapi.DSLoadLibrary(os.environ['DSHOME']+'/lib/libvmdsapi.so')
    dsapi.DSSetServerParams(DS_DOMAIN_NAME, DS_USER_NAME, DS_PASSWORD, DS_SERVER)
    hproj, err = dsapi.DSOpenProject(DS_PROJECT)
    if err:
      module.fail_json(msg="Failed to open the project {}: {}".format(DS_PROJECT,err), **result)
  
    if len(module.params['props']) == 0:
       module.warn('properties undefined')
       res, err = dsapi.DSListProjectProperties(hproj)
       if err:
         module.fail_json(msg="Failed to retrieve project properties {}: {}".format(DS_PROJECT,err), **result)
       props={}
       for var in res:
         props[var.split('=')[0]]='='.join(var.split('=')[1:])
    else:
        props = module.params['props']
    
    update = False
    result['skipped'] = False
    result['status'] = 'ok'
    result['property'] = DS_PROPERTY
    result['value'] = str(DS_VALUE)

    if DS_PROPERTY == 'Purges':
        if props['PurgeEnabled'] == '0':
            props['PurgeEnabled'] = 'FALSE'
        if props['DaysOld'] != '0':
            props['PurgeEnabled'] = 'TRUE -days '+props['DaysOld']
        if props['PrevRuns' ] != '0':
            props['PurgeEnabled'] = 'TRUE -runs '+props['PrevRuns']

    if not DS_PROPERTY in propertiesLabels:
        result['failed'] = True
        result['status'] = 'failed'
        module.fail_json(msg="Unknown property {}".format(DS_PROPERTY), **result)
    Property = propertiesLabels[DS_PROPERTY]
    if Property in resultsMap:
        try:
            DS_VALUE = resultsMap[Property][DS_VALUE]
        except:
            DS_VALUE = DS_VALUE
    if Property in props:
        if props[Property] != DS_VALUE:
            update = True
    else:
        result['failed'] = True
        result['status'] = 'failed'
        module.fail_json(msg="Unknown property {}".format(DS_PROPERTY), **result)
    
    if update:
        res,err = dsapi.DSSetProjectProperty(hproj,propertiesMap[Property],DS_VALUE)
        if err:
           module.fail_json(msg="Failed to set {}:{}".format(DS_PROPERTY,err), **result)
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
