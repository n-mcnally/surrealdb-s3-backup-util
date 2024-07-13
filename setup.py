from setuptools import setup, find_packages

setup(
    name='surreal-backup',
    version='1.0.0',
    description='Backup SurrealDB data to S3.',
    author='Maevia Digital Limited',
    author_email='webmaster@maevia.co.uk',
    packages=find_packages(),
    py_modules=['surreal_backup'],
    install_requires=[
        'boto3',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'surreal-backup=surreal_backup:main',
        ],
    },
)