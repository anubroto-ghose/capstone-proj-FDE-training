# Auth Service

Base path: `/api/v1/auth`

## Endpoints
- `POST /signup`: Create account with `first_name`, `last_name`, `email`, `password`, `role`.
- `POST /login`: Validate credentials and return JWT access token.

## Notes
- Passwords are stored as bcrypt hashes (`password_hash`).
- JWT payload includes `sub` (email), `role`, `iat`, and `exp`.
