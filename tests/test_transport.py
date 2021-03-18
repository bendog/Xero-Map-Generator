"""
Test transport functionality.
"""

from six import MovedModule, add_move

from xero_map_gen.transport import XeroApiWrapper
from .test_core import AbstractXMGTestCase

if True:
    add_move(MovedModule("mock", "mock", "unittest.mock"))
    from six.moves import mock

    from mock import patch, MagicMock


class TransportTestCase(AbstractXMGTestCase):
    def test_transport_basic(self):
        xero = XeroApiWrapper(**self.example_api_creds)
        self.assertTrue(xero)

    def test_get_contacts_by_ids(self):
        with patch.object(
            XeroApiWrapper,
            "rate_limit_retry_query",
            return_value=[self.example_api_contact],
        ):
            xero = XeroApiWrapper(**self.example_api_creds)
            contacts = xero.get_contacts_by_ids(
                ["a3e4631c-c02d-461d-a5ec-641c5aaace1f"], limit=1
            )

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].contact_id, "a3e4631c-c02d-461d-a5ec-641c5aaace1f")

    def test_get_contact_ids_in_group_ids(self):
        with patch.object(
            XeroApiWrapper,
            "rate_limit_retry_query",
            return_value=[
                {
                    "ContactGroupID": "4f935b4a-9406-41c0-ba45-b36b67c0123e",
                    "Contacts": [self.example_api_contact],
                    "HasValidationErrors": False,
                    "Name": "ACME Agencies",
                    "Status": "ACTIVE",
                }
            ],
        ):
            xero = XeroApiWrapper(**self.example_api_creds)
            ids = xero._get_contact_ids_in_group_ids(
                ["4f935b4a-9406-41c0-ba45-b36b67c0123e"]
            )
        self.assertEqual(ids, ["a3e4631c-c02d-461d-a5ec-641c5aaace1f"])

    def test_get_contact_group_ids_from_names(self):
        with patch.object(
            XeroApiWrapper,
            "rate_limit_retry_query",
            return_value=[
                {
                    "ContactGroupID": "4f935b4a-9406-41c0-ba45-b36b67c0123e",
                    "Contacts": [self.example_api_contact],
                    "HasValidationErrors": False,
                    "Name": "ACME Agencies",
                    "Status": "ACTIVE",
                }
            ],
        ):
            xero = XeroApiWrapper(**self.example_api_creds)
            ids = xero._get_contact_group_ids_from_names(["ACME Agencies"])
        self.assertEqual(ids, ["4f935b4a-9406-41c0-ba45-b36b67c0123e"])

    def test_get_contacts_in_group_names(self):
        with patch.object(
            XeroApiWrapper,
            "_get_contact_group_ids_from_names",
            return_value=["4f935b4a-9406-41c0-ba45-b36b67c0123e"],
        ), patch.object(
            XeroApiWrapper,
            "_get_contact_ids_in_group_ids",
            return_value=["a3e4631c-c02d-461d-a5ec-641c5aaace1f"],
        ), patch.object(
            XeroApiWrapper,
            "get_contacts_by_ids",
            return_value=[self.example_api_contact],
        ):
            xero = XeroApiWrapper(**self.example_api_creds)
            contacts = xero.get_contacts_in_group_names(["ACME Agencies"], limit=1)

        self.assertEqual(len(contacts), 1)

    def test_get_creds_file(self):
        api_creds = self.example_api_creds.copy()
        del api_creds["rsa_key_raw"]
        api_creds["rsa_key_path"] = "tests/sample_data/dummy_rsa_key.pem"
        xero = XeroApiWrapper(**api_creds)
        self.assertTrue(xero)
