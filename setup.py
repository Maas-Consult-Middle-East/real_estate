from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="real_estate",
    version="1.0.0",
    description="Comprehensive Real Estate and Property Management for ERPNext",
    author="Real Estate Module",
    author_email="support@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
