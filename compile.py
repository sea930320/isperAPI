import os
import sys
from py_compile import compile

print "argvs:",sys.argv

if len(sys.argv) == 3:
    comd = sys.argv[1]
    path = sys.argv[2]
    if os.path.exists(path) and os.path.isdir(path):
        for parent,dirname,filename in os.walk(path):
            for cfile in filename:
                fullname = os.path.join(parent,cfile)
                if comd == 'clean' and cfile[-4:] == '.pyc':
                    try:
                        os.remove(fullname)
                        print "Success remove file:%s" % fullname
                    except:
                        print "Can't remove file:%s" % fullname
                if comd == 'compile' and cfile[-3:] == '.py':
                    try:
                        compile(fullname)
                        print "Success compile file:%s" % fullname
                    except:
                        print "Can't compile file:%s" % fullname
                if comd == 'remove' and cfile[-3:] == '.py' and cfile != 'settings.py' and cfile != 'wsgi.py':
                    try:
                        os.remove(fullname)
                        print "Success remove file:%s" % fullname
                    except:
                        print "Can't remove file:%s" % fullname
    else:
        print "Not an directory or Direcotry doesn't exist!"
else:
    print "Usage:"
    print "\tpython compile_pyc.py clean PATH\t\t#To clean all pyc files"
    print "\tpython compile_pyc.py compile PATH\t\t#To generate pyc files"
    print "\tpython compile_pyc.py remove PATH\t\t#To remove py files"

    