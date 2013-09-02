include ../../../../Make.vars 

EXTRA_DIST =\
	meta.xml \
	__init__.py \
	pytutorial.py

if PY_ENABLED
AM_CPPFLAGS += $(PYTHON_CPPFLAGS)
endif # PY_ENABLED 

pkglib_LTLIBRARIES =		\
	tutorial.la

tutorial_la_CPPFLAGS = $(AM_CPPFLAGS) -I $(top_srcdir)/src/nox -I $(top_srcdir)/src/nox/coreapps/
tutorial_la_SOURCES = tutorial.cc
tutorial_la_LDFLAGS = -module -export-dynamic

NOX_RUNTIMEFILES = meta.json \
	__init__.py \
	pytutorial.py

all-local: nox-all-local
clean-local: nox-clean-local 
install-exec-hook: nox-install-local
