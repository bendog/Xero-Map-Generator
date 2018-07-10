""" Communication with various APIs. """
import pprint
import time
from builtins import super
import os

from xero import Xero
from xero.auth import PrivateCredentials
from xero.exceptions import XeroRateLimitExceeded

from .contain import XeroContact
from .log import PKG_LOGGER

class XeroApiWrapper(Xero):
    """ docstring for XeroApiWrapper. """
    sleep_time = 10
    max_attempts = 3

    def __init__(self, rsa_key_path, consumer_key):
        PKG_LOGGER.debug(
            "xero API args: rsa_key_path: %s; consumer_key: %s",
            rsa_key_path, consumer_key
        )
        rsa_key_path = os.path.expanduser(rsa_key_path)

        with open(rsa_key_path) as key_file:
            rsa_key = key_file.read()

        credentials = PrivateCredentials(consumer_key, rsa_key)
        super().__init__(credentials)

    def rate_limit_retry_get(self, attribute, *args, **kwargs):
        attempts = 0
        sleep_time = self.sleep_time
        while attempts < self.max_attempts:
            try:
                return getattr(self, attribute).get(*args, **kwargs)
            except XeroRateLimitExceeded:
                PKG_LOGGER.info("API rate limit reached. Sleeping for %s seconds" % sleep_time)
                attempts += 1
                time.sleep(sleep_time)
                sleep_time += self.sleep_time
                continue
        raise UserWarning("Reached maximum number attempts (%s) for GET %s" % (self.max_attempts, attribute))

    def get_contacts_by_ids(self, contact_ids, limit=None):
        limit = limit or None
        contacts = []
        for contact_id in contact_ids:
            if limit is not None and limit < 0:
                break
            try:
                api_contact_data = self.rate_limit_retry_get('contacts', contact_id)
            except Exception:
                break
            assert len(api_contact_data) == 1
            api_contact_data = api_contact_data[0]
            assert api_contact_data, "empty api response for contact id %s" % contact_id
            contact_obj = XeroContact(api_contact_data)
            PKG_LOGGER.debug("sanitized contact: %s", contact_obj)
            if not contact_obj.active:
                continue
            contacts.append(contact_obj)
            if limit is not None:
                limit -= 1
        return contacts

    def get_contacts_in_groups(self, names=None, contact_group_ids=None, limit=None):
        """
        Get all contacts within the union of the contact groups specified.

        Parameters
        ----------
        names : list
            a list of contact group names to filter on (case insensitive)
        contact_group_ids : list
            a list of contact group IDs to filter on. Overrides names
        """

        limit = limit or None
        names = names or []
        names_upper = [name.upper() for name in names]
        contact_group_ids = contact_group_ids or []
        assert any([names, contact_group_ids]), "either names or contact_group_ids must be specified"
        if not contact_group_ids:
            all_groups = self.contactgroups.all()
            PKG_LOGGER.debug("all xero contact groups: %s", pprint.pformat(all_groups))
            for contact_group in all_groups:
                if contact_group.get('Name', '').upper() not in names_upper:
                    continue
                contact_group_id = contact_group.get('ContactGroupID')
                if contact_group_id:
                    contact_group_ids.append(contact_group_id)
        assert contact_group_ids, "unable to find contact group ID matching any of %s" % names
        contact_ids = set()
        for contact_group_id in contact_group_ids:
            group_data = self.contactgroups.get(contact_group_id)[0]
            PKG_LOGGER.debug("group data: %s", pprint.pformat(group_data))
            for contact in group_data.get('Contacts', []):
                contact_id = contact.get('ContactID')
                if contact_id:
                    contact_ids.add(contact_id)
        return self.get_contacts_by_ids(contact_ids, limit)
