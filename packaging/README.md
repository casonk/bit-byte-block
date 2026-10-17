# RPM packaging

`bit-byte-block.spec` builds a noarch RPM for Fedora (and other distributions
with the `pyproject-rpm-macros` toolchain) from the GitHub release tarball. The
package installs:

| Path | What |
|---|---|
| `/usr/bin/bit-byte-block` | the command |
| `/usr/lib/systemd/system/bit-byte-block.service` | hardened service, not enabled by default |
| `/etc/bit-byte-block/bit-byte-block.env` | settings, kept on upgrade once edited |
| `/usr/lib/firewalld/services/bit-byte-block.xml` | firewalld service for the proxy port |

## Using the package

```bash
sudo dnf copr enable casonk/tools
sudo dnf install bit-byte-block
sudoedit /etc/bit-byte-block/bit-byte-block.env    # optional
sudo systemctl enable --now bit-byte-block
# Open the proxy port only in the zone of your trusted LAN or VPN interface.
# The zone is not always "home": Fedora Workstation puts LAN interfaces in
# FedoraWorkstation by default.
firewall-cmd --get-active-zones
sudo firewall-cmd --zone=ZONE --add-service=bit-byte-block --permanent
sudo firewall-cmd --reload
```

The service runs as a throwaway system user with no write access to the
filesystem; it only relays TCP between your miners and the pool. `journalctl
-u bit-byte-block` shows its log.

`bit-byte-block setup` and `miner configure` read manifests from a source
checkout, so with the RPM use the packaged service instead of `setup`.

## Building locally

```bash
sudo dnf install rpm-build rpmdevtools pyproject-rpm-macros python3-devel
rpmdev-setuptree
git archive --prefix=bit-byte-block-0.1.0/ -o ~/rpmbuild/SOURCES/bit-byte-block-0.1.0.tar.gz HEAD
rpmbuild -ba packaging/bit-byte-block.spec
```

Use `mock -r fedora-rawhide-x86_64 --rebuild ~/rpmbuild/SRPMS/*.src.rpm` to
build in a clean root the way COPR does.

## Releasing

1. Bump `version` in `pyproject.toml` and `Version` in the spec together (a
   test fails if they differ), and add a `%changelog` entry.
2. Publish the GitHub release `vX.Y.Z`. PyPI publishing runs from it, and the
   tag's tarball is the RPM's `Source0`.
3. COPR rebuilds from the spec (one-time setup below), or run
   `copr-cli buildscm --clone-url https://github.com/casonk/bit-byte-block --commit vX.Y.Z --spec packaging/bit-byte-block.spec --method rpkg casonk/tools`.

### One-time COPR setup

1. Sign in at <https://copr.fedorainfracloud.org> with a Fedora account and
   create the project `tools` with the Fedora releases to build for.
2. Add a package `bit-byte-block`: source type SCM, clone URL
   `https://github.com/casonk/bit-byte-block`, spec file
   `packaging/bit-byte-block.spec`, SRPM build method `rpkg`, auto-rebuild on.
3. Copy the project's GitHub webhook URL from its Integrations page into this
   repository's **Settings → Webhooks** (content type `application/json`,
   tag push events), so publishing a release starts the RPM build.
