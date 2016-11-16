from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name="pytest-browser",
    version='0.1.1',
    description='A pytest plugin for console based browser test selection'
                ' just after the collection phase',
    long_description=readme,
    license='MIT',
    author='Mehmet Gerceker',
    author_email='mehmetg@msn.com',
    url='https://github.com/mehmetg/pytest-browser',
    download_url='https://github.com/mehmetg/pytest-browser/tarball/0.1',
    platforms=['linux', 'macos'],
    packages=['browser'],
    entry_points={'pytest11': [
        'browser = browser.plugin'
    ]},
    zip_safe=False,
    install_requires=['pytest>=2.7.0', 'urwid>=1.3.1'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
    ],
    keywords="py.test pytest plugin browse interactive",
)
