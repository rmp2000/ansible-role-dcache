# dCache Ansible role

Deploys a standalone dCache 10.2.28 service on Ubuntu 22.04 using Java 17,
one storage pool and HTTPS WebDAV. PostgreSQL 14 is installed locally through
the existing `rmp2000/ansible-role-postgresql` role. The database contains the
Chimera namespace; file contents reside in `dcache_pool_path`.

Install dependencies with `ansible-galaxy install -r requirements.yml`.
Invoke the role as `dcache` with privilege escalation enabled. Required secrets:

```yaml
dcache_password: "provide-a-secret-of-at-least-12-characters"
dcache_database_password: "provide-a-different-database-secret"
```

Defaults are documented in `defaults/main.yml`. Set `dcache_manage_database: false`
and supply the database host, port, name, user and password to use a pre-created
external PostgreSQL database. Database schema initialization remains dCache's job.
Package version, URL and SHA256 must be changed together when upgrading.

HTTPS uses a certificate generated on the target host. Clients must trust
`/etc/dcache/tls/hostcert.pem`. Private keys and passwords are never committed.
WebDAV does not redirect transfers to additional pool ports. PostgreSQL listens
only on loopback in the default standalone configuration.

The default user is `dcacheuser`, with namespace directory `/data`. The default
endpoint is `https://HOST:2880/data/`. Supply persistent storage for the pool path
when required; retaining file contents also requires retaining the namespace
database. This initial single-machine deployment does not provide replication
or high availability.

The role checks the filesystem behind the pool parent directory before installing
dCache and rejects sizes below 1 GiB. Set `dcache_require_pool_mount: true` when
the parent must be a separate mount. The TOSCA recipe enables this check and
explicitly selects the additional disk device for its Ramses image. CI exercises
the guard with a real 1 MiB temporary filesystem.

## Verification

`tests/install.yml` installs the role and tests HTTPS upload/download, exact byte
equality, rejection of unauthenticated access, deletion and absence after deletion.
CI repeats the installation and requires zero changes. Test credentials are
explicitly non-production. The role performs the same functional check by default;
set `dcache_verify: false` to skip it during an already validated reconfiguration.

The local verification tool reads a JSON object with `endpoint`, `user`, `password`
and `ca` from stdin. Temporary test files are deleted even after a failed assertion.
No test removes user data.
