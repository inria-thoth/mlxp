

def pytest_exception_interact(node, call, report):
    excinfo = call.excinfo
    if 'script' in node.funcargs:
        excinfo.traceback = excinfo.traceback.cut(path=node.funcargs['script'])
    report.longrepr = node.repr_failure(excinfo)



