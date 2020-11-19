# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = auto/source
BUILDDIR      = auto/build

# Manuals
MANUALSRC		= ./manuals/source
MANUALOUT		= ./manuals
LATEXCOMMAND	= "/usr/bin/pdflatex"

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile pdf manuals stubs

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

pdf:
	@$(SPHINXBUILD) -b rinoh "$(SOURCEDIR)" auto/build/pdf

stubs:
	sphinx-apidoc -o auto/source/_stubs/ ../dataMole/ -f

clean:
	rm -rf auto/build

manuals:
	@$(LATEXCOMMAND) -synctex=1 -output-directory="$(MANUALOUT)" -interaction=nonstopmode  \
	"$(MANUALSRC)/dev-manual.tex" "$(MANUALSRC)/user-manual.tex"
