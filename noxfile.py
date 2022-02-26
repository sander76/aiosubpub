import nox


def install_flit_dev_deps(session):
    session.run("python", "--version")
    session.install("flit")
    session.run("flit", "install")
    # session.run("python", "-m", "pip", "install", "pip", "-U")
    # session.run("pip", "install", ".[dev,test]")


@nox.session(python=["3.7", "3.8", "3.9", "3.10"])
def tests(session):
    install_flit_dev_deps(session)
    session.run("pytest", "--cov=aiosubpub", "--cov-report=xml:cov.xml", "tests")
