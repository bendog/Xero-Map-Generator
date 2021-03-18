import datetime
import os
import shlex
import tempfile
import unittest

import pytest
from six import MovedModule, add_move
from traitlets.config.loader import Config

from . import TESTS_DATA_DIR
from xero_map_gen.config import load_cli_config, load_config, load_file_config
from xero_map_gen.contain import XeroContact
from xero_map_gen.core import dump_map_contacts, get_map_contacts
from xero_map_gen.log import PKG_LOGGER, setup_logging
from xero_map_gen.transport import XeroApiWrapper

if True:
    add_move(MovedModule("mock", "mock", "unittest.mock"))
    from six.moves import mock

    from mock import patch


@pytest.mark.usefixtures("debug")
class AbstractXMGTestCase(unittest.TestCase):
    config_dir = TESTS_DATA_DIR
    config_path = "config.json"
    override_args = ""
    debug = False

    example_api_contact = {
        "Addresses": [
            {
                "AddressType": "STREET",
                "AttentionTo": "",
                "City": "",
                "Country": "",
                "PostalCode": "",
                "Region": "",
            },
            {
                "AddressLine1": "9571 Mariners Cove Place",
                "AddressLine2": "",
                "AddressLine3": "",
                "AddressLine4": "",
                "AddressType": "POBOX",
                "AttentionTo": "John Smith",
                "City": "Sydney",
                "Country": "AU",
                "PostalCode": "1033",
                "Region": "NSW",
            },
        ],
        "Attachments": [],
        "BankAccountDetails": "",
        "ContactGroups": [
            {
                "ContactGroupID": "4f935b4a-9406-41c0-ba45-b36b67c0123e",
                "Contacts": [],
                "HasValidationErrors": False,
                "Name": "ACME Agencies",
                "Status": "ACTIVE",
            }
        ],
        "ContactID": "a3e4631c-c02d-461d-a5ec-641c5aaace1f",
        "ContactNumber": "",
        "ContactPersons": [],
        "ContactStatus": "ACTIVE",
        "DefaultCurrency": "AUD",
        "EmailAddress": "grohlfing0@reddit.com",
        "FirstName": "John",
        "HasAttachments": False,
        "HasValidationErrors": False,
        "IsCustomer": True,
        "IsSupplier": False,
        "LastName": "Smith",
        "Name": "Eare Pharmacy",
        "PaymentTerms": {"Sales": {"Day": 30, "Type": "DAYSAFTERBILLDATE"}},
        "Phones": [
            {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "",
                "PhoneType": "DDI",
            },
            {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891038",
                "PhoneType": "DEFAULT",
            },
            {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68892299",
                "PhoneType": "FAX",
            },
            {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "",
                "PhoneType": "MOBILE",
            },
        ],
        "TaxNumber": "27 604 367 587",
        "UpdatedDateUTC": datetime.datetime(2017, 2, 20, 18, 14, 30, 327000),
    }

    example_api_creds = {
        "consumer_key": "XXXXXXXXXXXXXXXXX1XXXX1XXX1XXX",
        "rsa_key_raw": "XXXXXXXXXX",
    }

    def setUp(self):
        config_paths = []
        if self.config_path:
            config_paths.append(self.config_path)
        proto_conf = Config()
        proto_conf.LogConfig = Config()
        if self.debug:
            proto_conf.LogConfig.stream_log_level = "DEBUG"
        else:
            proto_conf.LogConfig.stream_log_level = "WARNING"
        proto_conf.BaseConfig = Config()
        proto_conf.BaseConfig.config_dir = self.config_dir
        proto_conf.BaseConfig.config_path = self.config_path

        self.conf = load_config(shlex.split(self.override_args), proto_conf)

        setup_logging(**dict(self.conf.LogConfig))

        PKG_LOGGER.debug("Completed setUp of class %s", self.__class__.__name__)


class XMGCoreTestCase(AbstractXMGTestCase):
    def test_get_map_contacts(self):
        self.conf.FilterConfig.contact_groups = "Test"
        with patch.object(
            XeroApiWrapper,
            "get_contacts_in_group_names",
            return_value=[XeroContact(self.example_api_contact)],
        ):
            map_contacts = get_map_contacts(self.conf)
        self.assertEqual(len(map_contacts), 1)

    def test_get_map_contacts_state_filter(self):
        self.conf.FilterConfig.contact_groups = "Test"
        self.conf.FilterConfig.states = "NSW"
        with patch.object(
            XeroApiWrapper,
            "get_contacts_in_group_names",
            return_value=[XeroContact(self.example_api_contact)],
        ):
            map_contacts = get_map_contacts(self.conf)
        self.assertEqual(len(map_contacts), 1)

        self.conf.FilterConfig.states = "WA|VIC"
        with patch.object(
            XeroApiWrapper,
            "get_contacts_in_group_names",
            return_value=[XeroContact(self.example_api_contact)],
        ):
            map_contacts = get_map_contacts(self.conf)
        self.assertEqual(len(map_contacts), 0)

    def test_get_map_contacts_country_filter(self):
        self.conf.FilterConfig.contact_groups = "Test"
        self.conf.FilterConfig.countries = "Australia"
        with patch.object(
            XeroApiWrapper,
            "get_contacts_in_group_names",
            return_value=[XeroContact(self.example_api_contact)],
        ):
            map_contacts = get_map_contacts(self.conf)
        self.assertEqual(len(map_contacts), 1)

        self.conf.FilterConfig.countries = "USA"
        with patch.object(
            XeroApiWrapper,
            "get_contacts_in_group_names",
            return_value=[XeroContact(self.example_api_contact)],
        ):
            map_contacts = get_map_contacts(self.conf)
        self.assertEqual(len(map_contacts), 0)

    def test_dump_map_contacts(self):
        map_contacts = [XeroContact(self.example_api_contact)]

        tmp_dump_dir = tempfile.mkdtemp(self.id())
        self.conf.BaseConfig.dump_dir = tmp_dump_dir
        dump_map_contacts(self.conf, map_contacts)
        dump_dir_contents = os.listdir(tmp_dump_dir)
        self.assertEqual(len(dump_dir_contents), 1)
