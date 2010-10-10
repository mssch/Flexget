from paver.easy import *
import paver.virtual
import paver.setuputils
from paver import svn
from paver.setuputils import setup, find_package_data, find_packages

PROJECT_DIR = path(__file__).dirname()

options = environment.options
setup(
    name='FlexGet',
    version='1.0', # our tasks append the r1234 (current svn revision) to the version number
    description='FlexGet is a program aimed to automate downloading or processing content (torrents, podcasts, etc.) from different sources like RSS-feeds, html-pages, various sites and more.',
    author='Marko Koivusalo',
    author_email='marko.koivusalo@gmail.com',
    url='http://flexget.com',
    install_requires=['FeedParser', 'SQLAlchemy>0.5', 'PyYAML', 'BeautifulSoup', 'html5lib>=0.11', \
                      'PyRSS2Gen', 'pynzb', 'progressbar'],
    packages=['flexget', 'flexget.plugins', 'flexget.utils', 'flexget.utils.titles'],
    package_data=find_package_data('flexget', package='flexget', only_in_packages=False),
    zip_safe=False,
    test_suite='nose.collector',
    setup_requires=['nose>=0.11'],
    entry_points="""
        [console_scripts]
        flexget = flexget:main
    """
)
options(
    minilib=Bunch(
        extra_files=['virtual', 'svn']
    ),
    virtualenv=Bunch(
        packages_to_install=['nose>=0.11'],
        paver_command_line='develop',
        unzip_setuptools=True
    ),
    pylint = Bunch(
        check_modules = ['flexget'],
        quiet = False,
        verbose = False,
        quiet_args = ['--reports=no', '--disable-checker=similarities'],
        pylint_args = ['--rcfile=pylint.rc', '--include-ids=y'],
        ignore = False
    )
)

def freplace(name, what_str, with_str):
    """Replaces a :what_str: with :with_str: in file :name:"""
    import fileinput
    for line in fileinput.FileInput(name, inplace=1):
        if what_str in line:
            line = line.replace(what_str, with_str)
        print line,


@task
#@needs(['minilib', 'generate_setup', 'setuptools.command.sdist'])
def sdist():
    """Build tar.gz distribution package"""

    revision = svn.info().get('last_changed_rev')

    # clean previous build
    print 'Cleaning build...'
    for p in ['build']:
        pth = path(p)
        if pth.isdir():
            pth.rmtree()
        elif pth.isfile():
            pth.remove()
        else:
            print 'Unable to remove %s' % pth

    # remove pre-compiled pycs from tests, I don't know why paver even tries to include them ...
    # seems to happen only with sdist though
    for pyc in path('tests/').files('*.pyc'):
        pyc.remove()

    ver = '%sr%s' % (options['version'], revision)

    print 'Building %s' % ver

    # replace version number
    freplace('flexget/__init__.py', "__version__ = '{subversion}'", "__version__ = '%s'" % ver)

    # hack version number into setup( ... options='1.0' ...)
    from paver import tasks
    setup_section = tasks.environment.options.setdefault("setup", Bunch())
    setup_section.update(version=ver)

    for t in ['minilib', 'generate_setup', 'setuptools.command.sdist']:
        call_task(t)

    #egg_options = ['-d', '/var/www/flexget_dist/unstable'] # hmph, how can I pass params to it? doesn't seem to work ..
    #bdist_egg(egg_options)

    # restore version ...
    freplace('flexget/__init__.py', "__version__ = '%s'" % ver, "__version__ = '{subversion}'")


@task
@cmdopts([
    ('online', None, 'Run online tests')
])
def test(options):
    """Run FlexGet unit tests"""
    options.setdefault('test', Bunch())
    import nose
    from nose.plugins.manager import DefaultPluginManager

    cfg = nose.config.Config(plugins=DefaultPluginManager(), verbosity=2)

    argv = ['bin/paver']

    if not options.test.get('online'):
        argv.extend(['--attr=!online'])

    argv.append('-v')
    argv.append('--processes=4')
    argv.append('-x')

    return nose.run(argv=argv, config=cfg)


@task
def clean():
    """Cleans up the virtualenv"""
    for p in ('bin', 'build', 'dist', 'docs', 'include', 'lib', 'man',
            'share', 'FlexGet.egg-info', 'paver-minilib.zip', 'setup.py'):
        pth = path(p)
        if pth.isdir():
            pth.rmtree()
        elif pth.isfile():
            pth.remove()


@task
@needs(["minilib", "generate_setup", "setuptools.command.bdist_egg"])
def bdist_egg():
    pass

@task
def coverage():
    """Make coverage.flexget.com"""
    # --with-coverage --cover-package=flexget --cover-html --cover-html-dir /var/www/flexget_coverage/

    import nose
    from nose.plugins.manager import DefaultPluginManager

    cfg = nose.config.Config(plugins=DefaultPluginManager(), verbosity=2)
    argv = ['bin/paver']
    argv.extend(['--attr=!online'])
    argv.append('--with-coverage')
    argv.append('--cover-html')
    argv.extend(['--cover-package', 'flexget'])
    argv.extend(['--cover-html-dir', '/var/www/flexget_coverage/'])
    nose.run(argv=argv, config=cfg)

    print 'Coverage generated'


@task
@cmdopts([
    ('online', None, 'runs online unit tests'),
    ('dist-dir=', 'd', 'directory to put final built distributions in'),
    ('no-tests', None, 'skips unit tests')
])
def release(options):
    """Make a FlexGet release. Same as bdist_egg but adds version information."""
    options.setdefault('release', Bunch())
    # clean previous build
    print 'Cleaning build...'
    for p in ['build']:
        pth = path(p)
        if pth.isdir():
            pth.rmtree()
        elif pth.isfile():
            pth.remove()
        else:
            print 'Unable to remove %s' % pth

    revision = svn.info().get('last_changed_rev')
    ver = '%sr%s' % (options['version'], revision)

    # replace version number
    freplace('flexget/__init__.py', "__version__ = '{subversion}'", "__version__ = '%s'" % ver)

    # run unit tests
    if options.release.get('online'):
        options.setdefault('test', Bunch())['online'] = True
    if not options.release.get('no_tests'):
        if not test():
            print 'Unit tests did not pass'
            return
    import shutil
    shutil.copytree('FlexGet.egg-info', 'FlexGet.egg-info-backup')

    # hack version number into setup( ... options='1.0-svn' ...)
    from paver import tasks
    setup_section = tasks.environment.options.setdefault("setup", Bunch())
    setup_section.update(version=ver)

    if options.release.get('dist_dir'):
        options.setdefault('bdist_egg', Bunch())['dist_dir'] = options.release.dist_dir
    bdist_egg()

    # restore version ...
    freplace('flexget/__init__.py', "__version__ = '%s'" % ver, "__version__ = '{subversion}'")

    # restore egg info from backup
    print 'Removing FlexGet.egg-info ...'
    shutil.rmtree('FlexGet.egg-info')
    print 'Restoring FlexGet.egg-info'
    shutil.move('FlexGet.egg-info-backup', 'FlexGet.egg-info')


# TODO: I don't think it is working / needed anymore?
@task
@cmdopts([
    ('pylint-command=', 'c', 'Specify a custom pylint executable'),
    ('quiet', 'q', 'Disables a lot of the pylint output'),
    ('verbose', 'v', 'Enables detailed output'),
    ('ignore', 'i', 'Ignore PyLint errors')
])
def pylint(options):

    import os.path
    if not os.path.exists('bin/pylint'):
        raise paver.tasks.BuildFailure('PyLint not installed!\n'+\
                                       'Run bin/easy_install logilab.pylintinstaller\n' + \
                                       'Do not be alarmed by the errors it may give, it still works ..')


    """Check the source code using PyLint."""
    from pylint import lint

    # Initial command.
    arguments = []

    if options.pylint.quiet:
        arguments.extend(options.pylint.quiet_args)

    if 'pylint_args' in options.pylint:
        arguments.extend(list(options.pylint.pylint_args))

    if not options.pylint.verbose:
        arguments.append('--errors-only')

    # Add the list of paths containing the modules to check using PyLint.
    arguments.extend(str(PROJECT_DIR / module) for module in options.check_modules)

    # By placing run_pylint into its own function, it allows us to do dry runs
    # without actually running PyLint.
    def run_pylint():
        # Add app folder to path.
        sys.path.insert(0, PROJECT_DIR)

        print 'Running pylint (this may take a while)'
        # Runs the PyLint command.
        try:
            lint.Run(arguments)
        # PyLint will `sys.exit()` when it has finished, so we need to catch
        # the exception and process it accordingly.
        except SystemExit, exc:
            return_code = exc.args[0]
            if return_code != 0 and (not options.pylint.ignore):
                raise paver.tasks.BuildFailure('PyLint finished with a non-zero exit code')

    return dry('bin/pylint ' + ' '.join(arguments), run_pylint)


@task
def install_tools():
    """Install development / hudson tools and dependencies"""

    try:
        import pip
    except:
        print 'Unable to import pip, please install it'
        return

    try:
        import pylint
        print 'Pylint INSTALLED'
    except:
        pip.main(['install', 'pylint']) # OR instead of pylint logilab.pylintinstaller ?

    try:
        import coverage
        print 'Coverage INSTALLED'
    except:
        pip.main(['install', 'coverage'])

    try:
        import nosexcover
        print 'Nose-xcover INSTALLED'
    except:
        pip.main(['install', 'http://github.com/cmheisel/nose-xcover/zipball/master'])
