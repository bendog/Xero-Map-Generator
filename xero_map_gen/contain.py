""" Container classes and utilities for containing data. """

import heapq
from copy import copy
import csv
import tabulate


class XeroContactGroup(object):
    pass

class XeroContact(object):
    def __init__(self, data):
        self.update_data(data)

    def update_data(self, data):
        self._data = data
        self._main_address = None
        self._main_phone = None

    @property
    def main_address(self):
        if getattr(self, '_main_address', None):
            return self._main_address
        addresses = self._data.get('Addresses', [])
        if len(addresses) == 0:
            return
        if len(addresses) == 1:
            self._main_address = addresses[0]
            return self._main_address
        type_priority = ['POBOX', 'STREET', 'DELIVERY']
        nonblank_addresses = []
        blank_addresses = []
        for address in addresses:
            type = address.get('AddressType')
            try:
                priority = type_priority.index(type)
            except ValueError:
                priority = len(type_priority)
            if any([
                value for key, value in address.items() \
                if key.startswith("AddressLine")
            ]):
                heapq.heappush(nonblank_addresses, (priority, address))
                continue
            heapq.heappush(blank_addresses, (priority, address))
        if nonblank_addresses:
            _, self._main_address = heapq.heappop(nonblank_addresses)
            return self._main_address
        _, self._main_address = heapq.heappop(blank_addresses)
        return self._main_address

    @property
    def main_phone(self):
        if getattr(self, '_main_phone', None):
            return self._main_phone
        phones = self._data.get('Phones', [])
        if len(phones) == 0:
            return
        if len(phones) == 1:
            self._main_phone = phones[0]
            return self._main_phone
        type_priority = ['DEFAULT', 'DDI', 'MOBILE']
        nonblank_phones = []
        for phone in phones:
            type = phone.get('PhoneType')
            try:
                priority = type_priority.index(type)
            except ValueError:
                continue
            if phone.get('PhoneNumber'):
                heapq.heappush(nonblank_phones, (priority, phone))
                continue
        if nonblank_phones:
            _, self._main_phone = heapq.heappop(nonblank_phones)
            return self._main_phone

    @property
    def company_name(self):
        if 'Name' in self._data and self._data.get('Name') :
            return self._data['Name']

    @property
    def first_main_address_line(self):
        main_address = self.main_address
        for line in range(1, 5):
            key = "AddressLine%d" % line
            if key in self.main_address and self.main_address[key]:
                return self.main_address[key]

    @property
    def main_address_area(self):
        return self.main_address.get('City')

    @property
    def main_address_postcode(self):
        return self.main_address.get('PostalCode')

    @property
    def main_address_state(self):
        return self.main_address.get('Region')

    @classmethod
    def convert_country_code(cls, country_code):
        # TODO: complete this
        if country_code == 'AU':
            return 'Australia'
        return country_code

    @property
    def main_address_country(self):
        country_code = self.main_address.get('Country', '') or 'AU'
        return self.convert_country_code(country_code)

    @property
    def phone(self):
        main_phone = self.main_phone
        response = None
        if not main_phone.get('PhoneNumber'):
            return response
        response = main_phone['PhoneNumber']
        if not main_phone.get('PhoneAreaCode'):
            return response
        response = "%s %s" % (
            main_phone['PhoneAreaCode'],
            response
        )
        if not main_phone.get('PhoneCountryCode'):
            return response
        response = "(%s) %s" % (
            main_phone['PhoneCountryCode'],
            response
        )
        return response

    @property
    def archived(self):
        return self._data.get('ContactStatus') == 'ARCHIVED'

    @property
    def active(self):
        return self._data.get('ContactStatus') == 'ACTIVE'

    @property
    def contact_id(self):
        return self._data.get('ContactID')

    def flatten_raw(self):
        flattened = dict()
        for key in [
            'ContactID', 'ContactGroups', 'ContactNumber',
            'ContactStatus', 'EmailAddress', 'Name'
        ]:
            flattened[key] = self._data.get(key)
        for address in self._data['Addresses']:
            address = copy(address)
            type = address.pop('AddressType', 'POBOX')
            key = '%s Address' % type
            assert key not in flattened, "duplicate key being added"
            flattened[key] = address
        for phone in self._data['Phones']:
            phone = copy(phone)
            type = phone.pop('PhoneType', 'DEFAULT')
            key = '%s Phone' % type
            assert key not in flattened, "duplicate key being added"
            flattened[key] = phone
        return flattened

    def flatten_verbose(self):
        flattened = self.flatten_raw()
        for flat_key, attribute in [
            ('MAIN Address', 'main_address'),
            ('MAIN Phone', 'main_phone')
        ]:
            flattened[flat_key] = getattr(self, attribute)
        return flattened

    def flatten_sanitized(self):
        flattened = dict()
        for key in [
            'ContactID', 'EmailAddress', 'Name'
        ]:
            flattened[key] = self._data.get(key)

        for flat_key, attribute in [
            ('AddressLine', 'first_main_address_line'),
            ('AddressArea', 'main_address_area'),
            ('AddressPostcode', 'main_address_postcode'),
            ('AddressState', 'main_address_state'),
            ('AddressCountry', 'main_address_country'),
            ('Phone', 'phone'),
        ]:
            flattened[flat_key] = getattr(self, attribute)
        return flattened

    @classmethod
    def dump_contacts_raw_csv(cls, contacts, dump_path='contacts-raw.csv'):
        with open(dump_path, 'w') as dump_file:
            writer = csv.DictWriter(
                dump_file,
                {
                    'ContactID': 'ContactID',
                    'ContactGroups': 'ContactGroups',
                    'ContactNumber': 'ContactNumber',
                    'ContactStatus': 'ContactStatus',
                    'EmailAddress': 'EmailAddress',
                    'Name': 'Name',
                    'Address': 'Address',
                    'Phone': 'Phone',
                },
                extrasaction='ignore'
            )
            writer.writeheader()
            for contact in contacts:
                writer.writerow(contact.flatten_raw())

    @classmethod
    def dump_contacts_verbose_csv(cls, contacts, dump_path='contacts-verbose.csv'):
        with open(dump_path, 'w') as dump_file:
            writer = csv.DictWriter(
                dump_file,
                {
                    'ContactID': 'ContactID',
                    'ContactGroups': 'ContactGroups',
                    'ContactNumber': 'ContactNumber',
                    'ContactStatus': 'ContactStatus',
                    'EmailAddress': 'EmailAddress',
                    'Name': 'Name',
                    'MAIN Address': 'MAIN Address',
                    'POBOX Address': 'POBOX Address',
                    'STREET Address': 'STREET Address',
                    'DELIVERY Address': 'DELIVERY Address',
                    'MAIN Phone': 'Main Phone',
                    'DEFAULT Phone': 'DEFAULT Phone',
                    'DDI Phone': 'DDI Phone',
                    'MOBILE Phone': 'MOBILE Phone',
                    'FAX Phone': 'FAX Phone',
                },
                extrasaction='ignore'
            )
            writer.writeheader()
            for contact in contacts:
                writer.writerow(contact.flatten_verbose())

    @classmethod
    def dump_contacts_sanitized_csv(cls, contacts, dump_path='contacts-sanitized.csv'):
        with open(dump_path, 'w') as dump_file:
            writer = csv.DictWriter(
                dump_file,
                {
                    'ContactID': 'ContactID',
                    'EmailAddress': 'EmailAddress',
                    'Name': 'Name',
                    'AddressLine' : 'AddressLine',
                    'AddressArea' : 'AddressArea',
                    'AddressPostcode' : 'AddressPostcode',
                    'AddressState' : 'AddressState',
                    'AddressCountry' : 'AddressCountry',
                    'Phone' : 'Phone',
                },
                extrasaction='ignore'
            )
            writer.writeheader()
            for contact in contacts:
                writer.writerow(contact.flatten_sanitized())

    @classmethod
    def dump_contacts_sanitized_table(cls, contacts):
        return tabulate.tabulate(
            [contact.flatten_sanitized() for contact in contacts],
            headers='keys'
        )
