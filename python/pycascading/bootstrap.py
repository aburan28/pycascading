#
# Copyright 2011 Twitter, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Bootstrap the PyCascading script.

This is the main Python module that gets executed by Hadoop or in local mode.
The first command line argument is either 'local' or 'hadoop'. This determines
whether we're running the script in local mode or with Hadoop. For Hadoop we
need to pack the sources into a jar, which are extracted later to a temporary
directory, so we need to set up the search paths differently in this case.
"""

__author__ = 'Gabor Szabo'


import sys, imp

import org.slf4j.LoggerFactory
LOG = org.slf4j.LoggerFactory.getLogger("bootstrap.py")


if __name__ == "__main__":
    # The first command line parameter must be 'hadoop' or 'local'
    # to indicate the running mode
    running_mode = sys.argv[1]
    LOG.info("running mode: " + running_mode)

    # The second is the location of the PyCascading Python sources in local
    # mode, and the PyCascading tarball in Hadoop mode
    python_dir = sys.argv[2]
    LOG.info("PyCascading master dir: " + python_dir)

    # Remove the first two arguments so that sys.argv will look like as
    # if it was coming from a simple command line execution
    # The further parameters are the command line parameters to the script
    sys.argv = sys.argv[3:]

    from com.twitter.pycascading import Util

    # This is a list of jars that Cascading comes in
    cascading_jar = Util.getCascadingJar()
    LOG.info("Cascading JAR: " + ':'.join(cascading_jar))
    # This is the folder where Hadoop extracted the jar file for execution
    tmp_dir = Util.getJarFolder()
    LOG.info("Extracted job JAR: " + tmp_dir)

    Util.setPycascadingRoot(python_dir)

    # The initial value of sys.path is JYTHONPATH plus whatever Jython appends
    # to it (normally the Python standard libraries the come with Jython)
    sys.path.extend(cascading_jar)
    sys.path.extend((tmp_dir, python_dir + '/python',
                     python_dir + '/python/Lib', '.'))

    # Allow the importing of user-installed Jython packages
    import site
    site.addsitedir(python_dir + '/python/Lib/site-packages')

    #print 'PATH:', sys.path
    import os
    import encodings
    import pycascading.pipe, getopt

    # This holds some global configuration parameters
    pycascading.pipe.config = dict()

    opts, args = getopt.getopt(sys.argv, 'a:')
    pycascading.pipe.config['pycascading.distributed_cache.archives'] = []
    for opt in opts:
        if opt[0] == '-a':
            pycascading.pipe.config['pycascading.distributed_cache.archives'] \
            .append(opt[1])

    if running_mode == 'hadoop':
        # The folder where the sources were extracted to be run in Hadoop mode
        job_dir = args[0]
        # This is going to be seen by main()
        sys.argv = args[1:]
        main_file = args[1]
        physical_file = job_dir + '/' + args[1]
    else:
        main_file = args[0]
        physical_file = args[0]

    # It's necessary to put this import here, otherwise simplejson won't work.
    # Maybe it's automatically imported in the beginning of a Jython program,
    # but since at that point the sys.path is not set yet to Lib, it will fail?
    # Instead, we can use Java's JSON decoder...
#    import encodings

    # pycascading.pipe.config is a dict with configuration parameters
    pycascading.pipe.config['pycascading.running_mode'] = running_mode
    pycascading.pipe.config['pycascading.main_file'] = main_file

    # Import and run the user's script
    _main_module_ = imp.load_source('__main__', physical_file)
    _main_module_.main()
