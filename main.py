""" Main script for generating Map files. """
import os
import pprint
import sys

from xero_map_gen.config import load_config
from xero_map_gen.transport import XeroApiWrapper
from xero_map_gen.log import setup_logging, PKG_LOGGER
from xero_map_gen.contain import XeroContact

if __name__ == '__main__' and __package__ is None:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """ main. """
    conf = load_config()
    setup_logging(**dict(conf.LogConfig))
    PKG_LOGGER.info("final config is %s", pprint.pformat(conf))
    xero = XeroApiWrapper(**dict(conf.XeroApiConfig))
    map_contact_groups = conf.FilterConfig.contact_groups.split('|')
    PKG_LOGGER.debug("map contact groups: %s", map_contact_groups)
    contact_limit = conf.BaseConfig.contact_limit or None
    PKG_LOGGER.debug("contact limit: %s", contact_limit)
    map_contacts = xero.get_contacts_in_groups(names=map_contact_groups, limit=contact_limit)
    if conf.FilterConfig.states:
        # filter on state, warn if contact doesn't have state
        filter_states = [state.upper() for state in conf.FilterConfig.states.split('|')]
        filtered_contacts = []
        for contact in map_contacts:
            state = contact.main_address_state
            if not state:
                PKG_LOGGER.warn("Contact has no state set: %s" % contact.flatten_verbose())
                continue
            if state.upper() in filter_states:
                filtered_contacts.append(contact)
        map_contacts = filtered_contacts

    # TODO: validate addresses
    PKG_LOGGER.info("map contacts: \n%s", XeroContact.dump_contacts_sanitized_table(map_contacts))

    # XeroContact.dump_contacts_raw_csv(map_contacts)
    # XeroContact.dump_contacts_verbose_csv(map_contacts)
    XeroContact.dump_contacts_sanitized_csv(map_contacts, dump_path=conf.BaseConfig.dump_file)

    # import pudb; pudb.set_trace()

if __name__ == '__main__':
    main()
