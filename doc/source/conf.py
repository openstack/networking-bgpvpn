# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.blockdiag',
    'sphinxcontrib.seqdiag',
    #'sphinx.ext.intersphinx',
    'openstackdocstheme',
    'oslo_config.sphinxext',
    'oslo_config.sphinxconfiggen',
    'oslo_policy.sphinxext',
    'oslo_policy.sphinxpolicygen',
]

# openstackdocstheme options
openstackdocs_repo_name = 'openstack/networking-bgpvpn'
openstackdocs_pdf_link = True
openstackdocs_bug_project = 'bgpvpn'
openstackdocs_bug_tag = ''

# autodoc generation is a bit aggressive and a nuisance when doing heavy
# text edit cycles.
# execute "export SPHINX_DEBUG=1" in your terminal to disable

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
copyright = '2013, OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'native'

# Example configuration for intersphinx: refer to the Python standard library.
#intersphinx_mapping = {'http://docs.python.org/': None}

#blockdiag_antialias = True
seq_antialias = True
seqdiag_html_image_format = "svg"
blockdiag_html_image_format = "svg"

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
# html_theme = '_theme'
html_static_path = ['_static']
html_theme = 'openstackdocs'

# -- Options for LaTeX output -------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    ('index',
     'doc-networking-bgpvpn.tex',
     'Networking BGPVPN Documentation',
     'OpenStack Foundation', 'manual'),
]

latex_elements = {
    'extraclassoptions': 'openany,oneside',
}

# -- Options for oslo_config.sphinxconfiggen ---------------------------------

_config_generator_config_files = [
    'networking-bgpvpn.conf',
]

def _get_config_generator_config_definition(conf_file):
    config_file_path = '../../etc/oslo-config-generator/%s' % conf_file
    # oslo_config.sphinxconfiggen appends '.conf.sample' to the filename,
    # strip file extentension (.conf or .ini).
    output_file_path = '_static/config-samples/%s' % conf_file.rsplit('.', 1)[0]
    return (config_file_path, output_file_path)


config_generator_config_file = [
    _get_config_generator_config_definition(conf_file)
    for conf_file in _config_generator_config_files
]

# -- Options for oslo_policy.sphinxpolicygen ---------------------------------

policy_generator_config_file = '../../etc/oslo-policy-generator/policy.conf'
sample_policy_basename = '_static/networking-bgpvpn'
