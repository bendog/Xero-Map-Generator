""" Communication with various APIs. """
import pprint
import time
from builtins import super
import os
from tqdm import tqdm

from xero import Xero
from xero.auth import PrivateCredentials
from xero.exceptions import XeroRateLimitExceeded

from .contain import XeroContact
from .log import PKG_LOGGER, log_stream_quiet


class XeroApiWrapper(Xero):
    """ docstring for XeroApiWrapper. """

    sleep_time = 10
    max_attempts = 3

    def __init__(self, consumer_key, **kwargs):
        PKG_LOGGER.debug(
            "xero API args: consumer_key: %s, kwargs: %s", consumer_key, kwargs
        )
        rsa_key = kwargs.get("rsa_key_raw")
        if not rsa_key:
            rsa_key_path = kwargs.get("rsa_key_path")
            rsa_key_path = os.path.expanduser(rsa_key_path)

            with open(rsa_key_path) as key_file:
                rsa_key = key_file.read()

        credentials = PrivateCredentials(consumer_key, rsa_key)
        super().__init__(credentials)

    def rate_limit_retry_query(self, endpoint, query, *args, **kwargs):
        attempts = 0
        sleep_time = self.sleep_time
        while attempts < self.max_attempts:
            try:
                endpoint_obj = getattr(self, endpoint)
                return getattr(endpoint_obj, query)(*args, **kwargs)
            except XeroRateLimitExceeded:
                PKG_LOGGER.info(
                    "API rate limit reached. Sleeping for %s seconds" % sleep_time
                )
                attempts += 1
                time.sleep(sleep_time)
                sleep_time += self.sleep_time
                continue
        raise UserWarning(
            "Reached maximum number attempts (%s) for %s %s"
            % (self.max_attempts, query, endpoint)
        )

    def get_contacts_by_ids(self, contact_ids, limit=None, chunk_size=20):
        # TODO: local caching and check modified time
        limit = limit or None
        total = len(contact_ids)
        if limit is not None:
            total = min(total, limit)
        contacts = []
        with tqdm(total=total) as pbar:
            while contact_ids:
                if limit is not None:
                    if limit <= 0:
                        break
                    chunk_size = min(chunk_size, limit)
                query_contact_ids = contact_ids[:chunk_size]
                contact_ids = contact_ids[chunk_size:]
                filter_query = 'ContactStatus=="ACTIVE"&&(%s)' % "||".join(
                    ['ID==Guid("%s")' % contact_id for contact_id in query_contact_ids]
                )
                contacts_raw = self.rate_limit_retry_query(
                    "contacts", "filter", raw=filter_query
                )
                contacts.extend(
                    [XeroContact(contact_raw) for contact_raw in contacts_raw]
                )
                if limit is not None:
                    limit -= chunk_size
                if not log_stream_quiet():
                    pbar.update(chunk_size)
        return contacts

    def _get_contact_ids_in_group_ids(self, contact_group_ids=None, limit=None):
        contact_ids = set()
        for contact_group_id in contact_group_ids:
            group_data = self.rate_limit_retry_query(
                "contactgroups", "get", contact_group_id
            )[0]
            PKG_LOGGER.debug("group data: %s", pprint.pformat(group_data))
            for contact in group_data.get("Contacts", []):
                contact_id = contact.get("ContactID")
                if contact_id:
                    contact_ids.add(contact_id)
        return list(contact_ids)

    def _get_contact_group_ids_from_names(self, names):
        contact_group_ids = []
        names_upper = [name.upper() for name in names]
        all_groups = self.rate_limit_retry_query("contactgroups", "all")
        PKG_LOGGER.debug("all xero contact groups: %s", pprint.pformat(all_groups))
        for contact_group in all_groups:
            if contact_group.get("Name", "").upper() not in names_upper:
                continue
            contact_group_id = contact_group.get("ContactGroupID")
            if contact_group_id:
                contact_group_ids.append(contact_group_id)
        return contact_group_ids

    def get_contacts_in_group_names(self, names=None, limit=None):
        """
        Get all contacts within the union of the contact groups specified.

        Parameters
        ----------
        names : list
            a list of contact group names to filter on (case insensitive)
        contact_group_ids : list
            a list of contact group IDs to filter on. Overrides names
        """

        # TODO: this can easily be sped up with custom query

        limit = limit or None
        names = names or []
        contact_group_ids = self._get_contact_group_ids_from_names(names)
        assert contact_group_ids, (
            "unable to find contact group ID matching any of %s" % names
        )
        contact_ids = self._get_contact_ids_in_group_ids(contact_group_ids, limit)
        return self.get_contacts_by_ids(contact_ids, limit)
