# Authentication

Set a strong `SECRET_KEY` (`runapi init` generates one for you).

```python
from runapi import (
    create_access_token,
    create_refresh_token,
    verify_token,
    revoke_token,
    rotate_refresh_token,
    hash_password,
    verify_password,
)

access = create_access_token({"sub": "user-1"})
verify_token(access)  # payload dict, or None if invalid/expired/revoked
revoke_token(access)  # e.g. on logout

pair = rotate_refresh_token(refresh)  # {"access_token", "refresh_token"}; old refresh is revoked
```

Revocation uses an in-memory `TokenBlacklist`. With multiple workers, subclass it and back it with Redis or a database.

Passwords are hashed with bcrypt (`hash_password` / `verify_password`).
