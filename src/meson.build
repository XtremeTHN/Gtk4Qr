pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'dbusqrdecoder'

python = import('python')
python_i = python.find_installation('python3', modules: ['gi'])

conf = configuration_data()
conf.set('PYTHON', python_i.full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'dbusqrdecoder.in',
  output: 'dbusqrdecoder',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

nxloader_sources = [
  '__init__.py',
  'scanner.py',
  'main.py',
]

install_data(nxloader_sources, install_dir: moduledir)