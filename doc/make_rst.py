# -*- coding: utf-8 -*-
"""
    sphinx.apidoc
    ~~~~~~~~~~~~~

    Parses a directory tree looking for Python modules and packages and creates
    ReST files appropriately to create code documentation with Sphinx.  It also
    creates a modules index (named modules.<suffix>).

    This is derived from the "sphinx-autopackage" script, which is:
    Copyright 2008 Société des arts technologiques (SAT),
    http://www.sat.qc.ca/

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import sys
import optparse
from os import path

from sphinx.util.osutil import walk
from sphinx.ext.autosummary import get_documenter, import_by_name
from sphinx.util.inspect import safe_getattr

# automodule options
if 'SPHINX_APIDOC_OPTIONS' in os.environ:
    OPTIONS = os.environ['SPHINX_APIDOC_OPTIONS'].split(',')
else:
    OPTIONS = [
        'members',
        'undoc-members',
        'inherited-members',
        'show-inheritance',
    ]

INITPY = '__init__.py'
PY_SUFFIXES = set(['.py', '.pyx'])


def makename(package, module):
    """Join package and module with a dot."""
    # Both package and module can be None/empty.
    if package:
        name = package
        if module:
            name += '.' + module
    else:
        name = module
    return name


def write_file(name, text, opts):
    """Write the output file for module/package <name>."""
    fname = path.join(opts.destdir, '%s.%s' % (name, opts.suffix))
    if opts.dryrun:
        print 'Would create file %s.' % fname
        return
    if not opts.force and path.isfile(fname):
        print 'File %s already exists, skipping.' % fname
    else:
        print 'Creating file %s.' % fname
        f = open(fname, 'w')
        try:
            f.write(text)
        finally:
            f.close()


def format_heading(level, text):
    """Create a heading of <level> [1, 2 or 3 supported]."""
    underlining = ['=', '-', '~', ][level - 1] * len(text)
    return '%s\n%s\n\n' % (text, underlining)

def get_file(obj):
    if hasattr(obj, "__file__"):
        return obj.__file__
    if hasattr(obj, "__module__") and obj.__module__ is not None:
        name, module, parent = import_by_name(obj.__module__)
        return get_file(module)
    return None

def get_public_members(obj, typ, include_public=[]):
    items = []
    for name in dir(obj):
        attr = None
        try:
            attr = safe_getattr(obj, name)
            documenter = get_documenter(attr, obj)
        except AttributeError:
            continue
        
        attr_file = get_file(attr)
        if ((documenter.objtype == typ) 
                and ((attr_file == get_file(obj)) or (attr_file is None)) 
                and ((name in include_public) or not name.startswith('_'))):
            items.append(name)
    return items

def get_private_superclass_public_members(cls, typ):
    items = []
    if hasattr(cls, "__bases__"):
        for base in cls.__bases__:
            if base.__name__.startswith('_'):
                items.extend(get_public_members(base, typ))
                items.extend(get_private_superclass_public_members(base, typ))
    return items

def get_summary(items, title, indent, min_items=0):
    directive = ''
    if len(items) > min_items:
        directive += '%s.. rubric:: %s\n\n' % (indent, title)
        directive += '%s.. autosummary::\n' % indent
        for item in items:
            directive += '%s    %s\n' % (indent, item)
        directive += '\n'
    return directive

def split_into_abstract_and_non_abstract(cls, items, abstract_property):
    abstract = []
    non_abstract = []
    for item in items:
        obj = getattr(cls, item)
        if hasattr(obj, abstract_property):
            abstract.append(item)
        else:
            non_abstract.append(item)
    return abstract, non_abstract

def format_directive(module, package=None):
    """Create the automodule directive and add the options."""
    name, obj, parent = import_by_name(makename(package, module))
    functions = get_public_members(obj, 'function')
    classes = get_public_members(obj, 'class')
    exceptions = get_public_members(obj, 'exception')
    
    if len(functions) == 0 and len(classes) == 0 and len(exceptions) == 0:
        return None
    
    directive = '.. automodule:: %s\n\n' % makename(package, module)
    
    directive += '.. currentmodule:: %s\n\n' % makename(package, module)
    
    directive += get_summary(functions, "Functions", "")
    
    directive += get_summary(exceptions, "Exceptions", "", min_items=1)
    
    directive += get_summary(classes, "Classes", "", min_items=1)
            
    for function in functions:
        directive += '.. autofunction:: %s\n' % function
        
    for exception in exceptions:
        directive += '.. autoexception:: %s\n' % exception
    
    for cls in classes:
        directive += '.. autoclass:: %s\n' % cls
        directive += '    :show-inheritance:\n\n'
        
        cls_name, cls_obj, cls_parent = import_by_name(makename(package, 
                "%s.%s" % (module, cls)))
        attributes = get_public_members(cls_obj, 'attribute')
        methods = get_public_members(cls_obj, 'method')
        subclasses = get_public_members(cls_obj, 'class')
        attributes.extend(get_private_superclass_public_members(cls_obj, 
                'attribute'))
        methods.extend(get_private_superclass_public_members(cls_obj, 'method'))
        
        abstract_attrs, real_attrs = split_into_abstract_and_non_abstract(
                cls_obj, attributes, "__isabstractattribute__")
        abstract_methods, real_methods = split_into_abstract_and_non_abstract(
                cls_obj, methods, "__isabstractmethod__")
        
        directive += get_summary(abstract_attrs, "Abstract Attributes", "    ")
        
        directive += get_summary(real_attrs, "Attributes", "    ")
        
        directive += get_summary(abstract_methods, "Abstract Methods", "    ")
        
        directive += get_summary(real_methods, "Methods", "    ")
        
        if len(subclasses) > 0:
            directive += '    .. rubric:: Detailed Types\n\n'
            for subcls in subclasses:
                directive += '    .. autoattribute:: %s\n' % subcls
        
        if len(methods) > 0:
            directive += '    .. rubric:: Detailed Methods\n\n'
            for method in methods:
                directive += '    .. automethod:: %s\n' % method
            directive += '\n'
    
    return directive

def create_module_file(package, module, opts):
    """Build the text of the file and write the file."""
    #text += format_heading(2, ':mod:`%s` Module' % module)
    directive = format_directive(module, package)
    if directive is not None:
        if not opts.noheadings:
            text = format_heading(1, '%s module' % module)
        else:
            text = ''
        text += directive 
        write_file(makename(package, module), text, opts)


def create_package_file(root, master_package, subroot, py_files, opts, subs):
    """Build the text of the file and write the file."""
    text = format_heading(1, '%s package' % makename(master_package, subroot))

    # build a list of directories that are szvpackages (contain an INITPY file)
    subs = [sub for sub in subs if path.isfile(path.join(root, sub, INITPY))]
    # if there are some package directories, add a TOC for theses subpackages
    if subs:
        text += format_heading(2, 'Subpackages')
        text += '.. toctree::\n\n'
        for sub in subs:
            text += '    %s.%s\n' % (makename(master_package, subroot), sub)
        text += '\n'

    submods = [path.splitext(sub)[0] for sub in py_files
               if not shall_skip(path.join(root, sub), opts)
               and sub != INITPY]
    if submods:
        text += format_heading(2, 'Submodules')
        if opts.separatemodules:
            text += '.. toctree::\n\n'
            for submod in submods:
                modfile = makename(master_package, makename(subroot, submod))

                # generate separate file for this module
                directive = format_directive(makename(subroot, submod),
                                             master_package)
                if directive is not None:
                    text += '   %s\n' % modfile
                    if not opts.noheadings:
                        filetext = format_heading(1, '%s module' % modfile)
                    else:
                        filetext = ''
                    filetext += directive
                    write_file(modfile, filetext, opts)
        else:
            for submod in submods:
                directive = format_directive(makename(subroot, submod),
                                         master_package)
                if directive is not None:
                    modfile = makename(master_package, makename(subroot, submod))
                    if not opts.noheadings:
                        text += format_heading(2, '%s module' % modfile)
                    text += directive
                    text += '\n'
        text += '\n'

    directive = format_directive(subroot, master_package)
    if directive is not None:
        text += format_heading(2, 'Module contents')
        text += directive

    write_file(makename(master_package, subroot), text, opts)


def create_modules_toc_file(modules, opts, name='modules'):
    """Create the module's index."""
    text = format_heading(1, '%s' % opts.header)
    text += '.. toctree::\n'
    text += '   :maxdepth: %s\n\n' % opts.maxdepth

    modules.sort()
    prev_module = ''
    for module in modules:
        # look if the module is a subpackage and, if yes, ignore it
        if module.startswith(prev_module + '.'):
            continue
        prev_module = module
        text += '   %s\n' % module

    write_file(name, text, opts)


def shall_skip(module, opts):
    """Check if we want to skip this module."""
    # skip it if there is nothing (or just \n or \r\n) in the file
    if path.getsize(module) <= 2:
        return True
    # skip if it has a "private" name and this is selected
    filename = path.basename(module)
    if filename != '__init__.py' and filename.startswith('_') and \
        not opts.includeprivate:
        return True
    return False


def recurse_tree(rootpath, excludes, opts):
    """
    Look for every file in the directory tree and create the corresponding
    ReST files.
    """
    # check if the base directory is a package and get its name
    if INITPY in os.listdir(rootpath):
        root_package = rootpath.split(path.sep)[-1]
    else:
        # otherwise, the base is a directory with packages
        root_package = None

    toplevels = []
    followlinks = getattr(opts, 'followlinks', False)
    includeprivate = getattr(opts, 'includeprivate', False)
    for root, subs, files in walk(rootpath, followlinks=followlinks):
        # document only Python module files (that aren't excluded)
        py_files = sorted(f for f in files
                          if path.splitext(f)[1] in PY_SUFFIXES and
                          not is_excluded(path.join(root, f), excludes))
        is_pkg = INITPY in py_files
        if is_pkg:
            py_files.remove(INITPY)
            py_files.insert(0, INITPY)
        elif root != rootpath:
            # only accept non-package at toplevel
            del subs[:]
            continue
        # remove hidden ('.') and private ('_') directories, as well as
        # excluded dirs
        if includeprivate:
            exclude_prefixes = ('.',)
        else:
            exclude_prefixes = ('.', '_')
        subs[:] = sorted(sub for sub in subs if not sub.startswith(exclude_prefixes)
                         and not is_excluded(path.join(root, sub), excludes))

        if is_pkg:
            # we are in a package with something to document
            if subs or len(py_files) > 1 or not \
                shall_skip(path.join(root, INITPY), opts):
                subpackage = root[len(rootpath):].lstrip(path.sep).\
                    replace(path.sep, '.')
                create_package_file(root, root_package, subpackage,
                                    py_files, opts, subs)
                toplevels.append(makename(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == rootpath and root_package is None
            for py_file in py_files:
                if not shall_skip(path.join(rootpath, py_file), opts):
                    module = path.splitext(py_file)[0]
                    create_module_file(root_package, module, opts)
                    toplevels.append(module)

    return toplevels


def normalize_excludes(rootpath, excludes):
    """Normalize the excluded directory list."""
    return [path.normpath(path.abspath(exclude)) for exclude in excludes]


def is_excluded(root, excludes):
    """Check if the directory is in the exclude list.

    Note: by having trailing slashes, we avoid common prefix issues, like
          e.g. an exlude "foo" also accidentally excluding "foobar".
    """
    root = path.normpath(root)
    for exclude in excludes:
        if root == exclude:
            return True
    return False


def main(argv=sys.argv):
    """Parse and check the command line arguments."""
    parser = optparse.OptionParser(
        usage="""\
usage: %prog [options] -o <output_path> <module_path> [exclude_path, ...]

Look recursively in <module_path> for Python modules and packages and create
one reST file with automodule directives per package in the <output_path>.

The <exclude_path>s can be files and/or directories that will be excluded
from generation.

Note: By default this script will not overwrite already created files.""")

    parser.add_option('-o', '--output-dir', action='store', dest='destdir',
                      help='Directory to place all output', default='')
    parser.add_option('-d', '--maxdepth', action='store', dest='maxdepth',
                      help='Maximum depth of submodules to show in the TOC '
                      '(default: 4)', type='int', default=4)
    parser.add_option('-f', '--force', action='store_true', dest='force',
                      help='Overwrite existing files')
    parser.add_option('-l', '--follow-links', action='store_true',
                      dest='followlinks', default=False,
                      help='Follow symbolic links. Powerful when combined '
                      'with collective.recipe.omelette.')
    parser.add_option('-n', '--dry-run', action='store_true', dest='dryrun',
                      help='Run the script without creating files')
    parser.add_option('-e', '--separate', action='store_true',
                      dest='separatemodules',
                      help='Put documentation for each module on its own page')
    parser.add_option('-P', '--private', action='store_true',
                      dest='includeprivate',
                      help='Include "_private" modules')
    parser.add_option('-T', '--no-toc', action='store_true', dest='notoc',
                      help='Don\'t create a table of contents file')
    parser.add_option('-E', '--no-headings', action='store_true',
                      dest='noheadings',
                      help='Don\'t create headings for the module/package '
                           'packages (e.g. when the docstrings already contain '
                           'them)')
    parser.add_option('-s', '--suffix', action='store', dest='suffix',
                      help='file suffix (default: rst)', default='rst')
    parser.add_option('-F', '--full', action='store_true', dest='full',
                      help='Generate a full project with sphinx-quickstart')
    parser.add_option('-H', '--doc-project', action='store', dest='header',
                      help='Project name (default: root module name)')
    parser.add_option('-A', '--doc-author', action='store', dest='author',
                      type='str',
                      help='Project author(s), used when --full is given')
    parser.add_option('-V', '--doc-version', action='store', dest='version',
                      help='Project version, used when --full is given')
    parser.add_option('-R', '--doc-release', action='store', dest='release',
                      help='Project release, used when --full is given, '
                      'defaults to --doc-version')

    (opts, args) = parser.parse_args(argv[1:])

    if not args:
        parser.error('A package path is required.')

    rootpath, excludes = args[0], args[1:]
    if not opts.destdir:
        parser.error('An output directory is required.')
    if opts.header is None:
        opts.header = path.normpath(rootpath).split(path.sep)[-1]
    if opts.suffix.startswith('.'):
        opts.suffix = opts.suffix[1:]
    if not path.isdir(rootpath):
        print >>sys.stderr, '%s is not a directory.' % rootpath
        sys.exit(1)
    if not path.isdir(opts.destdir):
        if not opts.dryrun:
            os.makedirs(opts.destdir)
    rootpath = path.normpath(path.abspath(rootpath))
    excludes = normalize_excludes(rootpath, excludes)
    modules = recurse_tree(rootpath, excludes, opts)
    if opts.full:
        from sphinx import quickstart as qs
        modules.sort()
        prev_module = ''
        text = ''
        for module in modules:
            if module.startswith(prev_module + '.'):
                continue
            prev_module = module
            text += '   %s\n' % module
        d = dict(
            path = opts.destdir,
            sep  = False,
            dot  = '_',
            project = opts.header,
            author = opts.author or 'Author',
            version = opts.version or '',
            release = opts.release or opts.version or '',
            suffix = '.' + opts.suffix,
            master = 'index',
            epub = True,
            ext_autodoc = True,
            ext_viewcode = True,
            makefile = True,
            batchfile = True,
            mastertocmaxdepth = opts.maxdepth,
            mastertoctree = text,
        )
        if not opts.dryrun:
            qs.generate(d, silent=True, overwrite=opts.force)
    elif not opts.notoc:
        create_modules_toc_file(modules, opts)

if __name__ == "__main__":
    from sphinx.ext.autodoc import add_documenter, \
    ModuleDocumenter, ClassDocumenter, ExceptionDocumenter, DataDocumenter, \
    FunctionDocumenter, MethodDocumenter, AttributeDocumenter, \
    InstanceAttributeDocumenter
    add_documenter(ModuleDocumenter)
    add_documenter(ClassDocumenter)
    add_documenter(ExceptionDocumenter)
    add_documenter(DataDocumenter)
    add_documenter(FunctionDocumenter)
    add_documenter(MethodDocumenter)
    add_documenter(AttributeDocumenter)
    add_documenter(InstanceAttributeDocumenter)
    main()
