# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

import json
import hashlib
import base64
import base58
import time

from fetchai.ledger.crypto import Entity

def calc_resource_id(resource_address):
    hasher = hashlib.sha256()
    hasher.update(resource_address.encode())
    return base64.b64encode(hasher.digest()).decode()

def generate_token_address(muddle_address):
    raw_muddle_address = base64.b64decode(muddle_address)

    hasher1 = hashlib.sha256()
    hasher1.update(raw_muddle_address)
    token_address_base = hasher1.digest()

    hasher2 = hashlib.sha256()
    hasher2.update(token_address_base)
    token_address_checksum = hasher2.digest()[:4]

    final_address = token_address_base + token_address_checksum

    return base58.b58encode(final_address).decode()

def create_record(address, balance, stake):
    resource_id = calc_resource_id('fetch.token.state.' + address)
    resource_value = {"balance": balance, "stake": stake}
    return resource_id, resource_value

class GenesisFile():
    """
    Class for managing the creation of genesis files
    """

    def __init__(self, entities_with_wealth, entities_staking, max_cabinet_size, start_in, block_interval_ms):

        # All necessary parameters here
        self._entities_with_wealth = entities_with_wealth
        self._entities_staking     = entities_staking
        self._max_cabinet_size     = max_cabinet_size
        self._start_time           = int(time.time()) + start_in
        self._block_interval_ms    = block_interval_ms

        # Default parameters
        self._entropy_runahead     = 2
        self._aeon_periodicity     = 25
        self._aeon_offset          = 100
        self._minimum_stake        = 1000

    def as_json(self):

        stakes  = []
        state   = []

        # build up the configuration for all the stakers
        for (entity, amount) in self._entities_staking:
            token_address = generate_token_address(entity.public_key)

            # update the stake list
            stakes.append({
                'identity': pub_key,
                'amount': amount,
            })

        # build up the configuration for all the wallet holders
        for (entity, amount) in self._entities_with_wealth:
            token_address = generate_token_address(entity.public_key)

            # update the initial state
            key, value = create_record(
                token_address, amount, amount)
            state.append({
                "key": key,
                **value
            })

        # form the genesis data
        genesis_file = {
            'version': 3,
            'consensus': {
                'startTime': self._start_time,
                'cabinetSize': self._max_cabinet_size,
                'stakers': stakes,
                'entropyRunahead': self._entropy_runahead,
                'aeonPeriodicity': self._aeon_periodicity,
                'aeonOffset': self._aeon_offset,
                'minimumStake': self._minimum_stake,
            },
            'accounts': state,
        }

        return genesis_file

    def dump_to_file(self, file_name = "genesis_file.json", no_formatting = False):

        with open(file_name, 'w') as output_file:
            if no_formatting:
                json.dump(self.as_json(), output_file)
            else:
                json.dump(self.as_json(), output_file, indent=4, sort_keys=True)
