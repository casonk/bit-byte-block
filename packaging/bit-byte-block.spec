Name:           bit-byte-block
Version:        0.1.1
Release:        1%{?dist}
Summary:        Local Bitcoin Stratum proxy and upstream status tooling for solo.ckpool.org

License:        MIT
URL:            https://github.com/casonk/bit-byte-block
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-pytest
BuildRequires:  systemd-rpm-macros

# Runs from the standard library only; KeePassXC storage for `wallet generate
# --save` is optional and comes from auto-pass when it is installed.
Requires:       python3 >= 3.11
%{?systemd_requires}

%description
bit-byte-block runs a transparent Stratum proxy so the miners on a LAN or VPN
point at one stable local endpoint, with a primary and backup upstream pool. It
also reports solo.ckpool.org pool status and can generate a solo mining wallet.

The package installs the bit-byte-block command, a hardened systemd service
(not enabled by default), its settings in /etc/bit-byte-block, and a firewalld
service definition for the proxy port.

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files bit_byte_block
install -Dpm 0644 packaging/bit-byte-block.service %{buildroot}%{_unitdir}/bit-byte-block.service
install -Dpm 0644 packaging/bit-byte-block.firewalld.xml %{buildroot}%{_prefix}/lib/firewalld/services/bit-byte-block.xml
install -Dpm 0644 config/bit-byte-block.env.example %{buildroot}%{_sysconfdir}/bit-byte-block/bit-byte-block.env

%check
%pytest -q

%post
%systemd_post bit-byte-block.service

%preun
%systemd_preun bit-byte-block.service

%postun
%systemd_postun_with_restart bit-byte-block.service

%files -f %{pyproject_files}
%license LICENSE
%doc README.md CHANGELOG.md SECURITY.md
%{_bindir}/bit-byte-block
%{_unitdir}/bit-byte-block.service
%dir %{_prefix}/lib/firewalld
%dir %{_prefix}/lib/firewalld/services
%{_prefix}/lib/firewalld/services/bit-byte-block.xml
%dir %{_sysconfdir}/bit-byte-block
%config(noreplace) %{_sysconfdir}/bit-byte-block/bit-byte-block.env

%changelog
* Sat Oct 17 2026 Cason Konzer <casonk@umich.edu> - 0.1.1-1
- Accept the extra sections solo.ckpool.org now appends to its pool status

* Sat Oct 17 2026 Cason Konzer <casonk@umich.edu> - 0.1.0-1
- First package
