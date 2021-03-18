"""
Test container functionality.
"""

import unittest
import os

import pytest
import tempfile

from .test_core import AbstractXMGTestCase
from xero_map_gen.contain import XeroContact, XeroContactGroup


class ContainTestCase(AbstractXMGTestCase):
    pass


class XeroContactTestCase(ContainTestCase):
    # def setUp(self):
    #     super().setUp()

    # Data generated with https://mockaroo.com/4d8d5630

    def test_contact_basic(self):
        api_data = self.example_api_contact

        sanitized_data = {
            "Company Name": "Eare Pharmacy",
            "Address": "9571 Mariners Cove Place",
            "Area": "Sydney",
            "Postcode": "1033",
            "State": "NSW",
            "Country": "Australia",
            "Phone": "02 68891038",
        }

        contact = XeroContact(api_data)

        self.assertEqual(contact.company_name, sanitized_data["Company Name"])
        self.assertEqual(contact.main_address, api_data["Addresses"][1])
        self.assertEqual(contact.main_address_lines, sanitized_data["Address"])
        self.assertEqual(contact.main_address_area, sanitized_data["Area"])
        self.assertEqual(contact.main_address_postcode, sanitized_data["Postcode"])
        self.assertEqual(contact.main_address_state, sanitized_data["State"])
        self.assertEqual(contact.main_address_country, sanitized_data["Country"])
        self.assertEqual(contact.main_phone, api_data["Phones"][1])
        self.assertEqual(contact.phone, sanitized_data["Phone"])

    def test_contact_address_priority(self):
        """ Test that container chooses addresses in correct priority """
        addresses = [
            {
                "AddressLine1": "1 Mariners Cove Place",
                "AddressLine2": "",
                "AddressLine3": "",
                "AddressLine4": "",
                "AddressType": "DELIVERY",
                "AttentionTo": "John Smith",
                "City": "Sydney",
                "Country": "AU",
                "PostalCode": "1033",
                "Region": "NSW",
            },
            {
                "AddressLine1": "2 Mariners Cove Place",
                "AddressLine2": "",
                "AddressLine3": "",
                "AddressLine4": "",
                "AddressType": "STREET",
                "AttentionTo": "John Smith",
                "City": "Sydney",
                "Country": "AU",
                "PostalCode": "1033",
                "Region": "NSW",
            },
            {
                "AddressLine1": "3 Mariners Cove Place",
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
        ]
        for i in range(len(addresses)):
            api_data = {
                "Addresses": addresses[-i:] + addresses[:-i],
            }
            contact = XeroContact(api_data)
            self.assertEqual(contact.main_address, addresses[1])

    def test_contact_phone_priority(self):
        """ Test that container chooses addresses in correct priority """

        phones = [
            {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891030",
                "PhoneType": "DDI",
            },
            {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891031",
                "PhoneType": "DEFAULT",
            },
            {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891032",
                "PhoneType": "FAX",
            },
            {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891033",
                "PhoneType": "MOBILE",
            },
        ]
        for i in range(len(phones)):
            api_data = {
                "Phones": phones[-i:] + phones[:-i],
            }
            contact = XeroContact(api_data)
            self.assertEqual(contact.main_phone, phones[1])

    def test_dump_items_csv_unicode(self):
        tmp_dump_dir = tempfile.mkdtemp(self.id())
        items = [
            {
                "AddressPostcode": u"1234",
                "Name": u"Lil\u2019 Unicode",
                "AddressState": u"SA",
                "AddressCountry": "Australia",
                "Phone": u"08 1234 5678",
                "ContactID": u"f7b94e73-6846-4cc1-a91a-05aff537bf9e",
                "EmailAddress": u"blah@bigpond.com",
                "AddressArea": u"Unicodeland",
                "AddressLine": u"51 Derp Street",
            }
        ]
        dump_path = os.path.join(tmp_dump_dir, "items.csv")
        XeroContactGroup.dump_items_csv(
            items, dump_path=dump_path, names=XeroContactGroup.names_sanitized_csv
        )

        dump_dir_contents = os.listdir(tmp_dump_dir)
        self.assertEqual(len(dump_dir_contents), 1)

    def test_xero_contact_flatten_raw(self):
        contact = XeroContact(self.example_api_contact)
        flattened_raw = contact.flatten_raw()
        expected = {
            "ContactID": "a3e4631c-c02d-461d-a5ec-641c5aaace1f",
            "ContactGroups": [
                {
                    "ContactGroupID": "4f935b4a-9406-41c0-ba45-b36b67c0123e",
                    "Contacts": [],
                    "HasValidationErrors": False,
                    "Name": "ACME Agencies",
                    "Status": "ACTIVE",
                }
            ],
            "ContactNumber": "",
            "ContactStatus": "ACTIVE",
            "EmailAddress": "grohlfing0@reddit.com",
            "Name": "Eare Pharmacy",
            "Address STREET": {
                "AttentionTo": "",
                "City": "",
                "Country": "",
                "PostalCode": "",
                "Region": "",
            },
            "Address POBOX": {
                "AddressLine1": "9571 Mariners Cove Place",
                "AddressLine2": "",
                "AddressLine3": "",
                "AddressLine4": "",
                "AttentionTo": "John Smith",
                "City": "Sydney",
                "Country": "AU",
                "PostalCode": "1033",
                "Region": "NSW",
            },
            "Phone DDI": {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "",
            },
            "Phone DEFAULT": {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68891038",
            },
            "Phone FAX": {
                "PhoneAreaCode": "02",
                "PhoneCountryCode": "",
                "PhoneNumber": "68892299",
            },
            "Phone MOBILE": {
                "PhoneAreaCode": "",
                "PhoneCountryCode": "",
                "PhoneNumber": "",
            },
        }
        self.assertEqual(flattened_raw, expected)
