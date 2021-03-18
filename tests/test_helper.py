from __future__ import unicode_literals

from traitlets import TraitError

from xero_map_gen.helper import SanitationUtils, TraitValidation

from .test_core import AbstractXMGTestCase

from six import PY2, PY3


class HelperTestCase(AbstractXMGTestCase):
    def test_trait_validation(self):
        with self.assertRaises(TraitError):
            TraitValidation.path_exists("/nonexistent_path")

        with self.assertRaises(TraitError):
            TraitValidation.not_none(None)

        with self.assertRaises(TraitError):
            TraitValidation.not_falsey("")

        with self.assertRaises(TraitError):
            TraitValidation.not_falsey(0)

        with self.assertRaises(TraitError):
            TraitValidation.not_falsey(None)

        with self.assertRaises(TraitError):
            TraitValidation.not_falsey(False)

    def test_sanitation(self):
        as_ascii = SanitationUtils.to_ascii("\U000130ba")
        self.assertTrue(as_ascii.startswith("\\"))
