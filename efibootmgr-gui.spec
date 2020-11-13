Name:       efibootmgr-gui
Summary:    RPM package for efibootmgr-gui application
URL:        https://github.com/Elinvention/%{name}/

Version:    0.1
Release:    2%{?dist}
License:    GPLv3

Source0:    https://github.com/Elinvention/%{name}/archive/%{version}.tar.gz
BuildArch:  noarch
Requires:   python3 efibootmgr

%description
Manage EFI boot loader entries with this simple GUI.

%prep
%setup -q -n %{name}-%{version}

%install
install -dm 0755 %{buildroot}/%{_bindir}
install -m 0755 efibootmgr_gui.py %{buildroot}/%{_bindir}/%{name}
install -dm 0755 %{buildroot}/%{_datadir}/applications
install -m 0644 efibootmgr.desktop %{buildroot}/%{_datadir}/applications/%{name}.desktop

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%license LICENSE
%doc README.md

