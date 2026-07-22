"""Guard: the dev generators resolve their data root through the single seam.

If any of these modules ever reintroduces a hand-rolled ``Path(__file__).parent...``
root computation, this test fails — which is the whole point (see plan 006 / W1b).
"""

import omb.utils.class_page_generator as class_page_generator
import omb.utils.context_generator as context_generator
import omb.utils.properties_updater as properties_updater
import omb.utils.registry_updater as registry_updater
from omb.core.paths import builtin_data_root


def test_generators_resolve_root_through_builtin_data_root_seam():
    root = builtin_data_root()
    assert class_page_generator.ROOT_DIR == root
    assert context_generator.ROOT_DIR == root
    assert properties_updater.ROOT_DIR == root
    assert registry_updater.ROOT_DIR == root
