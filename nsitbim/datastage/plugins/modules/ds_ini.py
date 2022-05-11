#!/usr/bin/python

# Copyright: (c) 2020, NSIT BIM/Adrien Ferrara
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = '''
---
module: ds-ini

short_description: Gather ini file properties

version_added: '2.9.13'

description:  Returns ini file contents as an object

author:
    - NSIT BIM/Adrien Ferrara(@adrien-ferrara)
'''


from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        path=dict(type='str',required=True),
        configuration=dict(type='list',default=[])
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

    import ConfigParser
    result['status'] = 'ok'
    result['changed'] = False

    File = module.params['path']
    result['configuration'] = []
    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(File)
    for item in module.params['configuration']:
      conf = {}
      conf['name'] = item['name']
      conf['configuration'] = []
      options = {}
      for defoption in config.options(item['type']):
          options[defoption] = config.get(item['type'], defoption)
      for option in item['configuration']:
          options[option] = item['configuration'][option]
      conf['configuration'] = options.items()
      result['configuration'].append(conf)
          

    module.exit_json(**result)
def main():
    run_module()

if __name__ == '__main__':
    main()
