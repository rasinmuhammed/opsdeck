# fastapi-matrix-admin → opsdeck

This project has been **renamed to [opsdeck](https://pypi.org/project/opsdeck/)**.

This package is a compatibility shim: installing it installs `opsdeck` and
re-exports its API under the old `fastapi_matrix_admin` import path (including
the old `MatrixAdmin` class name), with a `DeprecationWarning`.

Migrate:

```bash
pip install opsdeck
```

```python
# before
from fastapi_matrix_admin import MatrixAdmin

# after
from opsdeck import OpsDeck
```

Docs: https://rasinmuhammed.github.io/opsdeck/
Source: https://github.com/rasinmuhammed/opsdeck
