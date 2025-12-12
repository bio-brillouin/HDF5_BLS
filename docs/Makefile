# Minimal Sphinx Makefile

SPHINXBUILD   = /Users/pierrebouvet/Documents/Code/Project_HDF5_BLS/.venv/bin/sphinx-build
SOURCEDIR     = .
BUILDDIR      = Tutorial

.PHONY: clean html latex latexpdf

clean:
	rm -rf $(BUILDDIR)/*

html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html

latex:
	# Corrected the output path to the conventional $(BUILDDIR)/latex
	$(SPHINXBUILD) -b latex $(SOURCEDIR) $(BUILDDIR)/latex

latexpdf: latex
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
# 	mv $(BUILDDIR)/latex/hdf5_bls.pdf $(BUILDDIR)/Tutorial.pdf