""" Container classes and utilities for containing data. """

import heapq

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
            return self._main_address
        phones = self._data.get('Addresses', [])
        if len(phones) == 0:
            return
        if len(phones) == 1:
            self._main_address = phones[0]
            return self._main_address
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

    @property
    def main_address_country(self):
        return self.main_address.get('Country')

    def to_dict(self):
        response = {}
        for key, value in dir(self):
            if key.startswith('_'):
                continue
            response[key] = value
