import nox


def install_flit_dev_deps(session):
    session.install("flit")
    session.run("flit", "install", "--deps", "develop")


@nox.session(python=["3.7", "3.8"])
def tests(session):
    install_flit_dev_deps(session)
    session.run("pytest", "--cov=aiosubpub", "--cov-report=xml:cov.xml", "tests")
