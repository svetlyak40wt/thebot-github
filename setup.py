from setuptools import setup

setup(
    name='thebot-github',
    version='0.1.0',
    description=(
    ),
    keywords='thebot github plugin',
    license = 'New BSD License',
    author="Alexander Artemenko",
    author_email='svetlyak.40wt@gmail.com',
    url='http://github.com/svetlyak40wt/thebot-github/',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Server',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
    ],
    py_modules=['thebot_github'],
    install_requires=[
        'thebot',
        'requests',
        'anyjson',
    ],
)
