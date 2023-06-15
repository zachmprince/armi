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

"""Module that tests methods within xsCollections."""
# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,invalid-name,no-self-use,no-method-argument,import-outside-toplevel
import os
import unittest

from armi import settings
from armi.reactor.blocks import HexBlock
from armi.nuclearDataIO import isotxs
from armi.nuclearDataIO import xsCollections
from armi.tests import ISOAA_PATH
from armi.utils.directoryChangers import TemporaryDirectoryChanger
from armi.utils.plotting import plotNucXs


class TestXsCollections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.microLib = isotxs.readBinary(ISOAA_PATH)

    def setUp(self):
        self.mc = xsCollections.MacroscopicCrossSectionCreator(
            minimumNuclideDensity=1e-13
        )
        self.block = MockBlock()
        self.block.setNumberDensity("U235", 0.02)
        self.block.setNumberDensity("FE", 0.01)

    def test_generateTotalScatteringMatrix(self):
        """Generates the total scattering matrix by summing elastic, inelastic, and n2n scattering matrices."""
        nuc = self.microLib.nuclides[0]
        totalScatter = nuc.micros.getTotalScatterMatrix()
        self.assertAlmostEqual(
            totalScatter[0, 0],
            (
                nuc.micros.elasticScatter[0, 0]
                + nuc.micros.inelasticScatter[0, 0]
                + 2.0 * nuc.micros.n2nScatter[0, 0]
            ),
        )

    def test_generateTotalScatteringMatrixWithMissingData(self):
        """
        Generates the total scattering matrix by summing elastic and n2n scattering matrices.

        Notes
        -----
        This tests that the total scattering matrix can be produced when the inelastic scattering matrix is not defined.
        """
        nuc = self.microLib.nuclides[0]
        nuc.micros.inelasticScatter = None
        totalScatter = nuc.micros.getTotalScatterMatrix()
        self.assertAlmostEqual(
            totalScatter[0, 0],
            (nuc.micros.elasticScatter[0, 0] + 2.0 * nuc.micros.n2nScatter[0, 0]),
        )

    def test_plotNucXs(self):
        """
        Testing this plotting method here because we need a XS library
        to run the test.
        """
        fName = "test_plotNucXs.png"
        with TemporaryDirectoryChanger():
            plotNucXs(self.microLib, "U235AA", "fission", fName=fName)
            self.assertTrue(os.path.exists(fName))

    def test_createMacrosFromMicros(self):
        self.assertEqual(self.mc.minimumNuclideDensity, 1e-13)
        self.mc.createMacrosFromMicros(self.microLib, self.block)
        totalMacroFissionXs = 0.0
        totalMacroAbsXs = 0.0
        for nuc, density in self.mc.densities.items():
            nuclideXS = self.mc.microLibrary.getNuclide(nuc, "AA")
            for microXs in nuclideXS.micros.fission:
                totalMacroFissionXs += microXs * density

            for microXsName in xsCollections.ABSORPTION_XS:
                for microXs in getattr(nuclideXS.micros, microXsName):
                    totalMacroAbsXs += microXs * density

        self.assertAlmostEqual(sum(self.mc.macros.fission), totalMacroFissionXs)
        self.assertAlmostEqual(sum(self.mc.macros.absorption), totalMacroAbsXs)

    def test_collapseCrossSection(self):
        """
        Tests cross section collapsing.

        Notes
        -----
        The expected 1 group cross section was generated by running the collapse cross section method. This tests
        that this method has not been modified to produce a different result.
        """
        expected1gXs = 2.35725262208
        micros = self.microLib["U235AA"].micros
        flux = list(reversed(range(33)))
        self.assertAlmostEqual(
            micros.collapseCrossSection(micros.nGamma, flux), expected1gXs
        )


class MockReactor:
    def __init__(self):
        self.blueprints = MockBlueprints()
        self.spatialGrid = None


class MockBlueprints:
    # this is only needed for allNuclidesInProblem and attributes were acting funky, so this was made.
    def __getattribute__(self, *args, **kwargs):
        return ["U235", "U235", "FE", "NA23"]


class MockBlock(HexBlock):
    def __init__(self, name=None, cs=None):
        self.density = {}
        HexBlock.__init__(self, name or "MockBlock", cs or settings.Settings())
        self.r = MockReactor()

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, r):
        self._r = r

    def getVolume(self, *args, **kwargs):
        return 1.0

    def getNuclideNumberDensities(self, nucNames):
        return [self.density.get(nucName, 0.0) for nucName in nucNames]

    def _getNdensHelper(self):
        return {nucName: density for nucName, density in self.density.items()}

    def setNumberDensity(self, key, val, *args, **kwargs):
        self.density[key] = val

    def getNuclides(self):
        return self.density.keys()
