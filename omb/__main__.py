#!/usr/bin/env python3
"""Enable ``python -m omb`` as an alias for the ``onto-validate`` console script.

Running ``python -m omb`` executes the validation suite CLI exactly as the
installed ``onto-validate`` entry point does, so the tool is usable immediately
after ``pip install`` without depending on the console-script shim being on PATH.

USAGE:
======
    python -m omb --run check-artifact-coherence --domain manifest
    python -m omb --data-paths ./my_data.json
"""

from omb.validators.validation_suite import main

if __name__ == "__main__":
    raise SystemExit(main())
