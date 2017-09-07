#!/usr/bin/python

##################################################
### DEBUG USING:
### ansible-playbook -i hosts site.yml --limit local --tags register-refelt-in-tangodb -vvv
##################################################


##################################################
###          MODULE IMPORT
##################################################
# Put any initial imports here - we can't use module.fail_json b/c we haven't
# imported stuff from ansible.module_utils.basic yet
# import configure_devices

#try:
#	## STANDARD MODULES
#    import json
#    import pkg_resources
#    import PyTango

#except ImportError, e:
#    print "failed=True msg='failed to import python module: %s'" % e
#    sys.exit(1)
##################################################
import json
import pkg_resources
import PyTango
import logging


DEFAULT_REFELT_ASTOR_CONFIG = dict(
#node: {level: (server/instance,server/instance,...)}
    { "levpro": {
        0: ("TangoAccessControl/1",),
    1: ("SvrFileLogger/Central",
        "SvrFileLogger/Elt"),
    2: ("SvrRefAchild/1",
        "SvrRefAchild/2"),
    3: ("SvrRefA/1",
        "SvrRefA/2"),
    5: ("SvrRefMaster/1",),
    },
    })

DEFAULT_REFELT_TANGO_CONFIG = dict(
#server_class: {server_instance: ((device_class,domain/family/instance),...)}
    { "SvrFileLogger" : {
          "Central": (("FileLogger", "ref/central/logger"),),
      "Elt": (("FileLogger", "ref/elt/logger"),),
      },
      "SvrRefA" : {
          "1": (("RefA", "ref/A/1"),),
          "2": (("RefA", "ref/A/2"),),
      },
      "SvrRefAchild" : {
          "1": (("RefAchild", "ref/achild/11"),
            ("RefAchild", "ref/achild/12"),),
          "2": (("RefAchild", "ref/achild/21"),
            ("RefAchild", "ref/achild/22"),),
      },
      "SvrRefMaster" : {
          "1": (("RefMaster","ref/elt/master"),),
      },
    })

def register_device(db, name, device_class, server_class, server_instance):
    dev_info = PyTango.DbDevInfo()
    dev_info.name = name
    dev_info._class = device_class
    dev_info.server = "{}/{}".format(server_class.split('.')[0], server_instance)
    print """Attempting to register TANGO device {!r}  class: {!r}  server: {!r}.""".format(
        dev_info.name, dev_info._class, dev_info.server)
    db.add_device(dev_info)

def register_in_tango(name, dbconfig):
    errors = 0
    done = 0
    db = PyTango.Database()
    out = ""
    #server_class: {server_instance: (class,domain/family/instance),...)}
    for server_class in sorted(dbconfig.keys()):
        for server_instance in dbconfig[server_class].keys():
            devices = dbconfig[server_class][server_instance]
            for device_class, device_name in devices:
                try:
                    register_device(db, device_name, device_class, server_class, server_instance)
                    logging.info("Registered {}".format(device_name))
                    done += 1
                    out = out + " " + device_name
                except Exception as exc:
                    logging.error("FAILED to registered {} {}".format(device_name, exc))
                    print """FAILED TO REGISTER in TANGO db"""
                    print """server_class={!r}  server_instance={!r} device_class={!r} device_name={!r}.""".format(
                        server_class, server_instance, device_class, device_name)
                    errors += 1
                    continue
    return errors, done, out

def register_in_astor(name, astorconfig):
    errors = 0
    done = 0
    out = "FAILED"
    print """FAILED TO REGISTER in ASTOR -- {}""".format(name)
    print astorconfig
    errors += 1
    return errors, done, out

##################################################
###          MODULE MAIN
##################################################
def main():
    """Main for the Ansible module"""

    ## Create ansible module
    changed = False
    message = ''

    module = AnsibleModule(
        argument_spec=dict(action=dict(required=True),
            facility_name=dict(required=True),
            facility_config=dict(required=True)),
            supports_check_mode=True
            )

    # In check mode, we take no action
    # Since this module never changes system state, we just
    # return changed=False
    if module.check_mode:
        module.exit_json(changed=False)

    ## Check if required parameters are provided
    # action, facility_name, facility_config
    if not module.params.get('action'):
        msg= "action parameter has to be specified!"
        module.fail_json(msg=msg)

    if not module.params.get('facility_name'):
        msg= "facility_name parameter has to be specified!"
        module.fail_json(msg=msg)

    if not module.params.get('facility_config'):
        msg= "facility_config parameter has to be specified!"
        module.fail_json(msg=msg)

    ## Get and check module args
    action = module.params['action']
    facility_name = module.params['facility_name']
    facility_config = module.params['facility_config']

    if action == "in_tangodb":
        if facility_config == "TBD":
            facility_config = DEFAULT_REFELT_TANGO_CONFIG
        errors, done, out = register_in_tango(facility_name, facility_config)
        msg = "Failed to register devices in TANGO db"
    elif action == "in_astor":
        if facility_config == "TBD":
            facility_config = DEFAULT_REFELT_ASTOR_CONFIG
        msg = "Failed to register servers in ASTOR"
        errors, done, out = register_in_astor(facility_name, facility_config)

    if errors:
        module.fail_json(msg=msg)
    else:
        module.exit_json(msg="Success {} done ({})".format(done, out),changed=True)


## Include at the end ansible (NB: it is not a standard Python include according to manual)
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
