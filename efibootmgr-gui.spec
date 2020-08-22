Name:       efibootmgr-gui
Summary:    RPM package for efibootmgr-gui application
URL:        https://github.com/Elinvention/%{name}/

Version:    0.1
Release:    1%{?dist}
License:    GPLv3

Source0:    https://github.com/Elinvention/%{name}/archive/%{version}.tar.gz
BuildArch:  noarch
Requires:   python3 efibootmgr

%description
Manage EFI boot loader entries with this simple GUI.

%prep
%setup -q -n %{name}-%{version}

%install
mkdir -p %{buildroot}/usr/bin/ %{buildroot}/usr/share/applications/
install -m 0755 efibootmgr_gui.py %{buildroot}/usr/bin/efibootmgr-gui
install -m 0644 efibootmgr.desktop %{buildroot}/usr/share/applications/efibootmgr-gui.desktop

%files
/usr/bin/efibootmgr-gui
/usr/share/applications/efibootmgr-gui.desktop
%license LICENSE
%doc README.md

