pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'efiboots'
gnome = import('gnome')

gnome.compile_resources('efiboots',
  'efiboots/efiboots.gresource.xml',
  source_dir: 'efiboots',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'efiboots.in',
  output: 'efiboots',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

efiboots_sources = [
  'efiboots/__init__.py',
  'efiboots/efibootmgr.py',
  'efiboots/main.py',
  'efiboots/utils.py',
  'efiboots/window.py',
  'efiboots/Efiboots.cmb',
]

install_data(efiboots_sources, install_dir: moduledir)
