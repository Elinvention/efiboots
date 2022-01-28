Name:    efiboots
Summary: RPM package for efiboots application
URL:     https://github.com/Elinvention/%{name}

Version: 1.0
Release: 1%{?dist}
License: GPLv3

Source0: %{URL}/archive/%{version}.tar.gz

BuildArch:     noarch
BuildRequires: python3-devel
BuildRequires: python3-rpm-macros
BuildRequires: %{py3_dist setuptools}

Requires: efibootmgr
Requires: python3
Requires: python3-gobject

%description
Manage EFI boot loader entries with this simple GUI.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build
%py3_build_egg

%install
%py3_install

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{python3_sitelib}/%{name}.py
%{python3_sitelib}/__pycache__/*.pyc
%{python3_sitelib}/%{name}-%{version}-py%{python3_version}.egg-info
%{_datadir}/applications/%{name}.desktop
%license LICENSE
%doc README.md
%exclude %{python3_sitelib}/test

%changelog
* Fri Jan 28 2022 sT331h0rs3 <sT331h0rs3@gmail.com> - 1.0-1
- Initial RPM packaging for Fedora is done.

