# Copyright 2019 TerraPower, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The depletion physics package contains utility/framework code related to the physics of transmutation and decay.
"""
import os

from armi import RES
from armi.nucDirectory import nuclideBases
from armi import interfaces

ORDER = interfaces.STACK_ORDER.DEPLETION


def applyDefaultBurnChain():
    """The framework has a default transmutation chain that many users will want to override."""
    with open(os.path.join(RES, "burn-chain.yaml")) as stream:
        nuclideBases.imposeBurnChain(stream)