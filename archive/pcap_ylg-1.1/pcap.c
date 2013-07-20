/*****************************************************************************
 * INCLUDED FILES & MACRO DEFINITIONS
 *****************************************************************************/

#include <Python.h>
#include <pcap/pcap.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#if defined(OS_LINUX)
#include <netpacket/packet.h>
#elif defined(OS_FREEBSD)
#include <net/if_dl.h>
#endif

#define PCAP_SNAPLEN_DFLT 65535

typedef struct {
    PyObject *user;
    pcap_t *pcap;
    PyObject *cb;
} PCAP_user_t;

/*****************************************************************************
 * GLOBAL VARIABLES
 *****************************************************************************/

static PyObject *PCAPError;
static char PCAPErrBuf[PCAP_ERRBUF_SIZE];

/*****************************************************************************
 * LOCAL FUNCTION DECLARATIONS
 *****************************************************************************/

static PyObject *__PCAPPktHdrToDict(const struct pcap_pkthdr *);
static int       __PCAPDictToPktHdr(PyObject *, struct pcap_pkthdr *);
static PyObject *__PCAPIfToDict(const pcap_if_t *);
static PyObject *__PCAPAddrToDict(const pcap_addr_t *);
static PyObject *__PCAPSockAddrToChar(const struct sockaddr *);
static PyObject *__PCAPObject_ld(
    PyObject *, PyObject *, const char *,
    int (*)(pcap_t *, int, pcap_handler, u_char *)
    );
static void      __PCAPHandler(
    u_char *, const struct pcap_pkthdr *, const u_char *
    );
static void      __PCAPAddConstant(PyObject *);
static PyObject *__PCAPAddrBinToTxt(const unsigned char *, size_t);

/*****************************************************************************
 * pcap.bpf_program OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(PCAPBPFProgramObjectDoc,
"bpf_program object is a wrapper for the type `struct bpf_program_t'\n\
used in PCAP library. Its methods are all PCAP library functions with\n\
prototype `type pcap_func(struct bpf_program_t *,...)'. Method names\n\
are functions names without `pcap_' prefix.\n\
\n\
Note: bpf_program object cannot be created directly. The only way to\n\
create such object is to use the `compile()' method of a pcap object\n\
instance.");

/* OBJECT */

typedef struct {
    PyObject_HEAD
    struct bpf_program bpfp;
} PCAPBPFProgramObject;

/* METHODS */

static PyObject *
PCAPBPFProgramObject_offline_filter(PCAPBPFProgramObject *self, PyObject *args)
{
    int ret;
    u_char *pkt;
    Py_ssize_t plen;
    PyObject *ohdr;
    struct pcap_pkthdr hdr;

    if (!PyArg_ParseTuple(
	    args, "O!s#:offline_filter", &PyDict_Type, &ohdr, &pkt, &plen))
	return NULL;
    if (__PCAPDictToPktHdr(ohdr, &hdr) < 0) {
	if (PyErr_ExceptionMatches(PyExc_TypeError))
	    PyErr_SetString(
		PyExc_TypeError,
		"offline_filter(): arg1 must be a dict of type:"
		" {'ts': {'tv_sec': <int>, 'tv_usec': <int>}, 'caplen': <int>,"
		" 'len': <int>}"
		);
	return NULL;
    }
    ret = pcap_offline_filter(&self->bpfp, &hdr, pkt);
    if (ret)
	Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyDoc_STRVAR(PCAPBPFProgramObject_offline_filter_doc,
"offline_filter(h, pkt) -> boolean\n\
\n\
offline_filter() check whether a filter matches a packet. It is a\n\
wrapper for pcap_offline_filter() Packet Capture library routine.\n\
\n\
Argument `h' must be a Python dictionary which is a wrapper for\n\
`struct pcap_pkthdr' defined in PCAP library. See `loop()' documentation\n\
for a description of this dictionary.\n\
Argument `pkt' is a (raw) string.");

static PyMethodDef PCAPBPFProgramObjectMethods[] = {
    {"offline_filter", (PyCFunction) PCAPBPFProgramObject_offline_filter,
     METH_VARARGS, PCAPBPFProgramObject_offline_filter_doc},
    {NULL, NULL, 0, NULL}
};

/* SPECIAL METHODS */

static void
PCAPBPFProgramObject_dealloc(PCAPBPFProgramObject *self)
{
    pcap_freecode(&self->bpfp);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *
PCAPBPFProgramObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(
	PCAPError, "`bpf_program' object cannot be created directly, "
	"use instead `compile()' method of a `pcap' object instance"
	);
    return NULL;
}

/* TYPE */

static PyTypeObject PCAPBPFProgramTypeObject = {
    PyObject_HEAD_INIT(NULL)
    0,						/* ob_size */
    "pcap.bpf_program",				/* tp_name */
    sizeof(PCAPBPFProgramObject),		/* tp_basicsize */
    0,						/* tp_itemsize */
    (destructor) PCAPBPFProgramObject_dealloc,	/* tp_dealloc */
    0,						/* tp_print */
    0,						/* tp_getattr */
    0,						/* tp_setattr */
    0,						/* tp_compare */
    0,						/* tp_repr */
    0,						/* tp_as_number */
    0,						/* tp_as_sequence */
    0,						/* tp_as_mapping */
    0,						/* tp_hash  */
    0,						/* tp_call */
    0,						/* tp_str */
    0,						/* tp_getattro */
    0,						/* tp_setattro */
    0,						/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    PCAPBPFProgramObjectDoc,			/* tp_doc */
    0,						/* tp_traverse */
    0,						/* tp_clear */
    0,						/* tp_richcompare */
    0,						/* tp_weaklistoffset */
    0,						/* tp_iter */
    0,						/* tp_iternext */
    PCAPBPFProgramObjectMethods,		/* tp_methods */
    0,						/* tp_members */
    0,						/* tp_getset */
    0,						/* tp_base */
    0,						/* tp_dict */
    0,						/* tp_descr_get */
    0,						/* tp_descr_set */
    0,						/* tp_dictoffset */
    0,						/* tp_init */
    0,						/* tp_alloc */
    (newfunc) PCAPBPFProgramObject_new,		/* tp_new */
};

/*****************************************************************************
 * pcap.pcap_dumper OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(PCAPDumperObjectDoc,
"pcap_dumper object is a wrapper for the type `pcap_dumper_t' defined\n\
in PCAP library. Its methods are all PCAP library functions with prototype\n\
`type pcap_func(pcap_dumper_t *,...)'. Method names are functions names\n\
without `pcap_' prefix.\n\
\n\
Note: pcap_dumper object cannot be created directly. The only way to\n\
create such object is to use the `dump_open()' method of a pcap object\n\
instance.");

/* OBJECT */

typedef struct {
    PyObject_HEAD
    pcap_dumper_t *pd;
    char *fn;
    PyFileObject *fo;
} PCAPDumperObject;

/* METHODS */

static PyObject *
PCAPDumperObject_dump_file(PCAPDumperObject *self)
{
    FILE *fp;

    fp = pcap_dump_file(self->pd);
    return PyFile_FromFile(fp, self->fn, "wb", NULL);
}

PyDoc_STRVAR(PCAPDumperObject_dump_file_doc,
"dump_file() -> file object\n\
\n\
dump_file() return the file object associated to standard I/O stream for\n\
a savefile being written. It is a wrapper for pcap_dump_file() Packet\n\
Capture library routine.");

static PyObject *
PCAPDumperObject_dump_flush(PCAPDumperObject *self)
{
    int ecode;

    ecode = pcap_dump_flush(self->pd);
    if (ecode < 0)
	return PyErr_Format(
	    PCAPError, "dump_flush(): pcap_dump_flush() failed"
	    );
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPDumperObject_dump_flush_doc,
"dump_flush() -> None\n\
\n\
dump_flush() flush to a savefile packets dumped. It is a wrapper\n\
for pcap_dump_flush() Packet Capture library routine.");

static PyObject *
PCAPDumperObject_dump_ftell(PCAPDumperObject *self)
{
    return Py_BuildValue("l", pcap_dump_ftell(self->pd));
}

PyDoc_STRVAR(PCAPDumperObject_dump_ftell_doc,
"dump_ftell() -> long\n\
\n\
dump_ftell() get the current file offset for a savefile being\n\
written. It is a wrapper for pcap_dump_ftell() Packet Capture\n\
library routine.");

static PyMethodDef PCAPDumperObjectMethods[] = {
    {"dump_file", (PyCFunction) PCAPDumperObject_dump_file,
     METH_NOARGS, PCAPDumperObject_dump_file_doc},
    {"dump_flush", (PyCFunction) PCAPDumperObject_dump_flush,
     METH_NOARGS, PCAPDumperObject_dump_flush_doc},
    {"dump_ftell", (PyCFunction) PCAPDumperObject_dump_ftell,
     METH_NOARGS, PCAPDumperObject_dump_ftell_doc},
    {NULL, NULL, 0, NULL}
};

/* SPECIAL METHODS */

static void
PCAPDumperObject_dealloc(PCAPDumperObject *self)
{
    if (self->pd) {
	(void ) pcap_dump_flush(self->pd);
	pcap_dump_close(self->pd);
    }
    PyMem_Free((void *) self->fn);
    if (self->fo)
	PyFile_DecUseCount(self->fo);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *
PCAPDumperObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyErr_SetString(
	PCAPError, "`pcap_dumper' object cannot be created directly, "
	"use instead `dump_open()' method of a `pcap' object instance"
	);
    return NULL;
}

/* TYPE */

static PyTypeObject PCAPDumperTypeObject = {
    PyObject_HEAD_INIT(NULL)
    0,						/* ob_size */
    "pcap.pcap_dumper",				/* tp_name */
    sizeof(PCAPDumperObject),			/* tp_basicsize */
    0,						/* tp_itemsize */
    (destructor) PCAPDumperObject_dealloc,	/* tp_dealloc */
    0,						/* tp_print */
    0,						/* tp_getattr */
    0,						/* tp_setattr */
    0,						/* tp_compare */
    0,						/* tp_repr */
    0,						/* tp_as_number */
    0,						/* tp_as_sequence */
    0,						/* tp_as_mapping */
    0,						/* tp_hash  */
    0,						/* tp_call */
    0,						/* tp_str */
    0,						/* tp_getattro */
    0,						/* tp_setattro */
    0,						/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    PCAPDumperObjectDoc,			/* tp_doc */
    0,						/* tp_traverse */
    0,						/* tp_clear */
    0,						/* tp_richcompare */
    0,						/* tp_weaklistoffset */
    0,						/* tp_iter */
    0,						/* tp_iternext */
    PCAPDumperObjectMethods,			/* tp_methods */
    0,						/* tp_members */
    0,						/* tp_getset */
    0,						/* tp_base */
    0,						/* tp_dict */
    0,						/* tp_descr_get */
    0,						/* tp_descr_set */
    0,						/* tp_dictoffset */
    0,						/* tp_init */
    0,						/* tp_alloc */
    (newfunc) PCAPDumperObject_new,		/* tp_new */
};

/*****************************************************************************
 * pcap.pcap OBJECT
 *****************************************************************************/

/* DOC */

PyDoc_STRVAR(PCAPObjectDoc,
"pcap object is a wrapper for the type `pcap_t' defined in PCAP\n\
library. Its methods are all PCAP library functions with prototype\n\
`type pcap_func(pcap_t *,...)'. Method names are functions names\n\
without `pcap_' prefix.");

/* OBJECT */

typedef struct {
    PyObject_HEAD
    pcap_t *pcap;
    char *fn;
    PyFileObject *fo;
} PCAPObject;

/* METHODS */

static PyObject *
PCAPObject_file(PCAPObject *self)
{
    FILE *fp;

    fp = pcap_file(self->pcap);
    if (!fp || !self->fn)
	Py_RETURN_NONE;
    return PyFile_FromFile(fp, self->fn, "wb", NULL);
}

PyDoc_STRVAR(PCAPObject_file_doc,
"file() -> file object | None\n\
\n\
file() get the file object associated to standard I/O stream for a \n\
savefile being read. It is a wrapper for pcap_file() Packet Capture\n\
library routine.\n\
\n\
Note: return None if pcap object was not opened with `pcap_offline()'");

static PyObject *
PCAPObject_fileno(PCAPObject *self)
{
    int fileno;

    fileno = pcap_fileno(self->pcap);
    if (fileno < 0) 
	return PyErr_Format(PCAPError, "fileno() failed");
    return Py_BuildValue("i", fileno);
}

PyDoc_STRVAR(PCAPObject_fileno_doc,
"fileno() -> int\n\
\n\
fileno() get the file descriptor for a live capture. It is a wrapper\n\
for pcap_fileno() Packet Capture library routine.");

static PyObject *
PCAPObject_dump_open(PCAPObject *self, PyObject *args)
{
    const char *fname;
    char *fn;
    pcap_dumper_t *pd;
    PCAPDumperObject *ret;

    if (!PyArg_ParseTuple(args, "s:dump_open", &fname))
	return NULL;
    pd = pcap_dump_open(self->pcap, fname);
    if (!pd)
	return PyErr_Format(
	    PCAPError, "dump_open(): %s", pcap_geterr(self->pcap)
	    );
    fn = (char *) PyMem_Malloc(strlen(fname) + 1);
    if (!fn) {
	pcap_dump_close(pd);
	return PyErr_NoMemory();
    }
    (void) strcpy(fn, fname);
    ret = PyObject_New(PCAPDumperObject, &PCAPDumperTypeObject);
    if (!ret) {
	pcap_dump_close(pd);
	PyMem_Free((void *) fn);
	return NULL;
    }
    ret->pd = pd;
    ret->fn = fn;
    ret->fo = NULL;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAPObject_dump_open_doc,
"dump_open(fname) -> pcap_dumper object\n\
\n\
dump_open() open a file to which to write packets. It is a wrapper for\n\
pcap_dump_open() Packet Capture library routine.");

static PyObject *
PCAPObject_dump_fopen(PCAPObject *self, PyObject *args)
{
    char *fn, *fname;
    FILE *fp;
    pcap_dumper_t *pd;
    PyFileObject *fo;
    PCAPDumperObject *ret;

    if (!PyArg_ParseTuple(args, "O!:dump_fopen", &PyFile_Type, &fo))
	return NULL;
    fp = PyFile_AsFile((PyObject *) fo);
    PyFile_IncUseCount(fo);
    pd = pcap_dump_fopen(self->pcap, fp);
    if (!pd) {
	PyFile_DecUseCount(fo);
	return PyErr_Format(
	    PCAPError, "dump_fopen(): %s", pcap_geterr(self->pcap)
	    );
    }
    fname = PyString_AS_STRING(PyFile_Name((PyObject *) fo));
    fn = (char *) PyMem_Malloc(strlen(fname) + 1);
    if (!fn) {
	pcap_dump_close(pd);
	Py_INCREF(fo);
	PyFile_DecUseCount(fo);
	return PyErr_NoMemory();
    }
    (void) strcpy(fn, fname);
    ret = PyObject_New(PCAPDumperObject, &PCAPDumperTypeObject);
    if (!ret) {
	pcap_dump_close(pd);
	Py_INCREF(fo);
	PyFile_DecUseCount(fo);
	PyMem_Free((void *) fn);
	return NULL;
    }
    ret->pd = pd;
    ret->fn = fn;
    Py_INCREF(fo);
    ret->fo = fo;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAPObject_dump_fopen_doc,
"dump_fopen(fp) -> pcap_dumper object\n\
\n\
dump_fopen() open a file to which to write packets. It is a wrapper for\n\
pcap_dump_fopen() Packet Capture library routine.\n\
\n\
Argument `fp' is a file object. File object `fp' should have been opened\n\
with mode `wb'.");

static PyObject *
PCAPObject_getnonblock(PCAPObject *self)
{
    int ret;

    ret = pcap_getnonblock(self->pcap, PCAPErrBuf);
    if (ret < 0)
	return PyErr_Format(PCAPError, "getnonblock(): %s", PCAPErrBuf);
    if (ret)
	Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyDoc_STRVAR(PCAPObject_getnonblock_doc,
"getnonblock() -> boolean\n\
\n\
getnonblock() get the state of non-blocking mode on a capture device.\n\
It is a wrapper for pcap_getnonblock() Packet Capture library routine.");

static PyObject *
PCAPObject_setnonblock(PCAPObject *self, PyObject *args)
{
    int nonblock, ret;
    PyObject *ononblock;

    if (!PyArg_ParseTuple(args, "O!:setnonblock", &PyBool_Type, &ononblock))
	return NULL;
    nonblock = ononblock == Py_False ? 0 : 1;
    ret = pcap_setnonblock(self->pcap, nonblock, PCAPErrBuf);
    if (ret < 0)
	return PyErr_Format(PCAPError, "setnonblock(): %s", PCAPErrBuf);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_setnonblock_doc,
"setnonblock(boolean) -> None\n\
\n\
setnonblock() set the state of non-blocking mode on a capture device.\n\
It is a wrapper for pcap_setnonblock() Packet Capture library routine.");

static PyObject *
PCAPObject_dispatch(PCAPObject *self, PyObject *args)
{
    return __PCAPObject_ld((PyObject *) self, args, "dispatch", pcap_dispatch);
}

PyDoc_STRVAR(PCAPObject_dispatch_doc,
"dispatch(cnt, callback [, user]) -> int\n\
\n\
dispatch() process packets from a live capture or savefile. It is a wrapper\n\
for pcap_dispatch() Packet Capture library routine. See `loop()' method.");

static PyObject *
PCAPObject_loop(PCAPObject *self, PyObject *args)
{
    return __PCAPObject_ld((PyObject *) self, args, "loop", pcap_loop);
}

PyDoc_STRVAR(PCAPObject_loop_doc,
"loop(cnt, callback [, user]) -> None\n\
\n\
loop() process packets from a live capture or savefile. It is a wrapper\n\
for pcap_loop() Packet Capture library routine.\n\
\n\
Argument `callback' is a function or an instance method which takes\n\
exactly 3 arguments. First one is the third argument of `loop' (`user')\n\
which is passed by `loop' to `callback'. It can be any Python object\n\
and it's default value is None. Second argument is a wrapper for\n\
`struct pcap_pkthdr' defined in PCAP library. It is a dictionary of\n\
the following form:\n\
  {'caplen': <int>, # length of portion present\n\
   'ts': {'tv_sec': <int>, 'tv_usec': <int>}, # time stamp\n\
   'len': <int> # length of this packet (off wire)\n\
  }\n\
Last argument of `callback' is a Python string containing the first\n\
`caplen' bytes of captured packet.");

static PyObject *
PCAPObject_next(PCAPObject *self)
{
    const u_char *pkt;
    struct pcap_pkthdr hdr;
    PyObject *ohdr;

    pkt = pcap_next(self->pcap, &hdr);
    if (!pkt)
	Py_RETURN_NONE;
    ohdr = __PCAPPktHdrToDict((const struct pcap_pkthdr *) &hdr);
    if (!ohdr)
	return NULL;
    return Py_BuildValue("Os#", ohdr, pkt, hdr.caplen);
}

PyDoc_STRVAR(PCAPObject_next_doc,
"next() -> (dict, str) | None\n\
\n\
next() read the next packet from a pcap object. It is a wrapper for\n\
pcap_next() Packet Capture library routine.\n\
\n\
Returned value is a 2-tuple. First element is a Python dictionary\n\
which is a wrapper for `struct pcap_pkthdr' defined in PCAP library\n\
(see `loop()' documentation for a description of this dictionary) and\n\
second element is a Python string containing the captured packet.\n\
\n\
next() returns None when pcap_next() returned NULL.");

static PyObject *
PCAPObject_next_ex(PCAPObject *self)
{
    int ecode;
    char *err;
    const u_char *pkt;
    struct pcap_pkthdr *hdr;
    PyObject *ohdr;

    ecode = pcap_next_ex(self->pcap, &hdr, &pkt);
    switch (ecode) {
    case -2:
	err = "next_ex(): no more packets to read from the savefile";
	break;
    case -1:
	(void ) snprintf(
	    PCAPErrBuf, sizeof(PCAPErrBuf), "next_ex(): %s",
	    pcap_geterr(self->pcap)
	    );
	err = PCAPErrBuf;
	break;
    case 0:
	err = "next_ex(): timeout expired";
	break;
    case 1:
	ohdr = __PCAPPktHdrToDict((const struct pcap_pkthdr *) hdr);
	if (!ohdr)
	    return NULL;
	break;
    default: /* should not happen */
	PyErr_SetString(PCAPError, "next_ex(): unexpected error");
	return NULL;
    }
    if (ecode != 1)
	return Py_BuildValue("(iOs)", ecode, Py_None, err);
    return Py_BuildValue("(iOs#)", ecode, ohdr, pkt, hdr->caplen);
}

PyDoc_STRVAR(PCAPObject_next_ex_doc,
"next_ex() -> (int, dict, str)\n\
\n\
next_ex() read the next packet from a pcap object. It is a wrapper for\n\
pcap_next_ex() Packet Capture library routine.\n\
\n\
Returned value is a 3-tuple. First element is a Python integer which\n\
is the integer returned by PCAP library function pcap_next_ex().\n\
\n\
If this integer is 1 (no error), second element is a Python dictionary\n\
which is a wrapper for `struct pcap_pkthdr' defined in PCAP library\n\
(see `loop()' documentation for a description of this dictionary) and\n\
last element is a Python string containing the captured packet.\n\
\n\
When pcap_next_ex() returns a value different from one (error occured),\n\
second element is setted to None and last element is a Python string\n\
containing the corresponding error message.");

static PyObject *
PCAPObject_inject(PCAPObject *self, PyObject *args)
{
    int ret, size;
    const char *buf;

    if (!PyArg_ParseTuple(args, "s#:inject", &buf, &size))
	return NULL;
    ret = pcap_inject(self->pcap, (const void *) buf, (size_t) size);
    if (ret < 0)
	return PyErr_Format(
	    PCAPError, "inject(): %s", pcap_geterr(self->pcap)
	    );
    return Py_BuildValue("i", ret);
}

PyDoc_STRVAR(PCAPObject_inject_doc,
"inject(pkt) -> int\n\
\n\
inject() transmit a packet. It is a wrapper for pcap_inject()\n\
Packet Capture library routine.");

static PyObject *
PCAPObject_sendpacket(PCAPObject *self, PyObject *args)
{
    int ecode, size;
    const char *buf;

    if (!PyArg_ParseTuple(args, "s#:sendpacket", &buf, &size))
	return NULL;
    ecode = pcap_sendpacket(self->pcap, (const u_char *) buf, size);
    if (ecode < 0)
	return PyErr_Format(
	    PCAPError, "sendpacket(): %s", pcap_geterr(self->pcap)
	    );
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_sendpacket_doc,
"sendpacket(pkt) -> None\n\
\n\
inject() transmit a packet. It is a wrapper for pcap_sendpacket()\n\
Packet Capture library routine.");

static PyObject *
PCAPObject_compile(PCAPObject *self, PyObject *args)
{
    int ecode, optimize;
    const char *str, *nm = NULL;
    bpf_u_int32 netmask = 0;
    PyObject *ooptimize = Py_True;
    PCAPBPFProgramObject *ret;

    if (!PyArg_ParseTuple(
	    args, "s|O!s:compile", &str, &PyBool_Type, &ooptimize, &nm))
	return NULL;
    if (nm)
	if (inet_pton(AF_INET, nm, (void *) &netmask) != 1)
	    return PyErr_Format(
		PCAPError, "compile(): `%s': invalid netmask", nm 
		);
    ret = PyObject_New(PCAPBPFProgramObject, &PCAPBPFProgramTypeObject);
    if (!ret)
	return NULL;
    optimize = ooptimize == Py_False ? 0 : 1;
    ecode = pcap_compile(self->pcap, &ret->bpfp, str, optimize, netmask);
    if (ecode < 0) {
	PyObject_Del((PyObject *) ret);
	return PyErr_Format(
	    PCAPError, "compile(): %s", pcap_geterr(self->pcap)
	    );
    }
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAPObject_compile_doc,
"compile(str [, optimize, netmask]) -> bpf_program object\n\
\n\
compile() compile a filter expression. It is a wrapper for pcap_compile()\n\
Packet Capture library routine.\n\
\n\
Default values for parameters `optimize' and `netmask' are respectively\n\
True and 0.");

static PyObject *
PCAPObject_setfilter(PCAPObject *self, PyObject *args)
{
    int ecode;
    PCAPBPFProgramObject *obpfp;

    if (!PyArg_ParseTuple(
	    args, "O!:setfilter", &PCAPBPFProgramTypeObject, &obpfp))
	return NULL;
    ecode = pcap_setfilter(self->pcap, &obpfp->bpfp);
    if (ecode < 0)
	return PyErr_Format(
	    PCAPError, "setfilter(): %s", pcap_geterr(self->pcap)
	    );
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_setfilter_doc,
"setfilter(fp) -> None\n\
\n\
setfilter() set the filter. It is a wrapper for pcap_setfilter()\n\
Packet Capture library routine.\n\
\n\
Argument `fp' is a bpf_program object, usually the result of a call to\n\
compile().");

static PyObject *
PCAPObject_setdirection(PCAPObject *self, PyObject *args)
{
    int d;

    if (!PyArg_ParseTuple(args, "i:setdirection", &d))
	return NULL;
    switch (d) {
    case PCAP_D_IN:
    case PCAP_D_OUT:
    case PCAP_D_INOUT:
    {
	int ecode;

	ecode = pcap_setdirection(self->pcap, (pcap_direction_t) d);
	if (ecode < 0)
	    return PyErr_Format(
		PCAPError, "setdirection(): %s", pcap_geterr(self->pcap)
		);
	Py_RETURN_NONE;
    }
    default:
	return PyErr_Format(
	    PyExc_TypeError,
	    "setdirection(): arg1 must be "
	    "%d (PCAP_D_INOUT), %d (PCAP_D_IN) or %d (PCAP_D_OUT)",
	    PCAP_D_INOUT, PCAP_D_IN, PCAP_D_OUT
	    );
    }
}

PyDoc_STRVAR(PCAPObject_setdirection_doc,
"setdirection(pcap.PCAP_D_IN | pcap.PCAP_D_OUT | pcap.PCAP_D_INOUT)\n\
   -> None\n\
\n\
setdirection() set the direction for which packets will be captured.\n\
It is a wrapper for pcap_setdirection() Packet Capture library routine.");

static PyObject *
PCAPObject_breakloop(PCAPObject *self)
{
    pcap_breakloop(self->pcap);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_breakloop_doc,
"breakloop() -> None\n\
\n\
breakloop() force a dispatch() or loop() call to return. It is a\n\
wrapper for pcap_breakloop() Packet Capture library routine.");

static PyObject *
PCAPObject_datalink(PCAPObject *self)
{
    return Py_BuildValue("i", pcap_datalink(self->pcap));
}

PyDoc_STRVAR(PCAPObject_datalink_doc,
"datalink() -> int\n\
\n\
datalink() get the link-layer header type. It is a wrapper for\n\
pcap_datalink() Packet Capture library routine.");

static PyObject *
PCAPObject_list_datalinks(PCAPObject *self)
{
    int i, size, *dlt_buf;
    PyObject *ret;
    
    size = pcap_list_datalinks(self->pcap, &dlt_buf);
    if (size < 0)
	return PyErr_Format(
	    PCAPError, "list_datalinks(): pcap_list_datalinks() failed"
	    );
    ret = PyTuple_New((Py_ssize_t) size);
    if (!ret) {
	free((void *) dlt_buf);
	return NULL;
    }
    for (i = 0; i < size; i++) {
	PyObject *val = Py_BuildValue("i", dlt_buf[i]);

	if (!val) {
	    free((void *) dlt_buf);
	    Py_DECREF(ret);
	    return NULL;
	}
	PyTuple_SET_ITEM(ret, (Py_ssize_t) i, val);
    }
    free((void *) dlt_buf);
    return ret;
}

PyDoc_STRVAR(PCAPObject_list_datalinks_doc,
"list_datalinks() -> (int, int,...)\n\
\n\
list_datalinks() get a list of link-layer header types supported\n\
by a capture device. It is a wrapper for pcap_list_datalinks()\n\
Packet Capture library routine.");

static PyObject *
PCAPObject_snapshot(PCAPObject *self)
{
    return Py_BuildValue("i", pcap_snapshot(self->pcap));
}

PyDoc_STRVAR(PCAPObject_snapshot_doc,
"snapshot() -> int\n\
\n\
snapshot() get the snapshot length. It is a wrapper for pcap_snapshot()\n\
Packet Capture library routine.");

static PyObject *
PCAPObject_is_swapped(PCAPObject *self)
{
    if (pcap_is_swapped(self->pcap))
	Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyDoc_STRVAR(PCAPObject_is_swapped_doc,
"is_swapped() -> boolean\n\
\n\
is_swapped() find out whether a savefile has the native byte order.\n\
It is a wrapper for pcap_is_swapped() Packet Capture library routine.");

static PyObject *
PCAPObject_major_version(PCAPObject *self)
{
    return Py_BuildValue("i", pcap_major_version(self->pcap));
}

PyDoc_STRVAR(PCAPObject_major_version_doc,
"major_version() -> int\n\
\n\
major_version() get the version number of a savefile. It is a wrapper\n\
for pcap_major_version() Packet Capture library routine.");

static PyObject *
PCAPObject_minor_version(PCAPObject *self)
{
    return Py_BuildValue("i", pcap_minor_version(self->pcap));
}

PyDoc_STRVAR(PCAPObject_minor_version_doc,
"minor_version() -> int\n\
\n\
minor_version() get the version number of a savefile. It is a wrapper\n\
for pcap_minor_version() Packet Capture library routine.");

static PyObject *
PCAPObject_stats(PCAPObject *self)
{
    int ecode;
    struct pcap_stat ps;

    ecode = pcap_stats(self->pcap, &ps);
    if (ecode < 0)
	return PyErr_Format(
	    PCAPError, "stats(): %s", pcap_geterr(self->pcap)
	    );
    return Py_BuildValue(
	"{sIsI}", "ps_recv", ps.ps_recv, "ps_drop", ps.ps_drop
	);
}

PyDoc_STRVAR(PCAPObject_stats_doc,
"stats() -> dict\n\
\n\
stats() get capture statistics. It is a wrapper for pcap_stats()\n\
Packet Capture library routine.\n\
\n\
Returned dictionary has following format:\n\
  {'ps_recv': <int>, # number of packets received\n\
   'ps_drop': <int>  # number of packets dropped\n\
  }");

static PyObject *
PCAPObject_activate(PCAPObject *self)
{
    int ecode;
    PyObject *ret;

    ecode = pcap_activate(self->pcap);
    switch (ecode) {
    case 0:
	Py_INCREF(Py_None);
	ret = Py_None;
	break;
    case PCAP_WARNING:
    case PCAP_WARNING_PROMISC_NOTSUP:
    {
	char *err = "activate(): ", *perr = pcap_geterr(self->pcap),
	    buf[strlen(err) + strlen(perr) + 1];

	(void) sprintf(buf, "%s%s", err, perr);
	(void) PyErr_WarnEx(PyExc_UserWarning, buf, 1);
	Py_INCREF(Py_None);
	ret = Py_None;
	break;
    }
    case PCAP_ERROR:
    case PCAP_ERROR_NO_SUCH_DEVICE:
    case PCAP_ERROR_PERM_DENIED:
	ret = PyErr_Format(
	    PCAPError, "activate(): %s", pcap_geterr(self->pcap));
	break;
    case PCAP_ERROR_ACTIVATED:
	ret = PyErr_Format(
	    PCAPError, "activate(): capture handle has already been activated");
	break;
    case PCAP_ERROR_RFMON_NOTSUP:
	ret = PyErr_Format(
	    PCAPError,
	    "activate(): capture source doesn't support monitor mode");
	break;
    case PCAP_ERROR_IFACE_NOT_UP:
	ret = PyErr_Format(
	    PCAPError, "activate(): capture source is not up");
	break;
    default:
	ret = PyErr_Format(
	    PCAPError, "activate(): %d: unexpected error code", ecode);
    }
    return ret;
}

PyDoc_STRVAR(PCAPObject_activate_doc,
"activate() -> None\n\
\n\
activate() activate a capture handle. It is a wrapper for pcap_activate()\n\
Packet Capture library routine.\n\
\n\
");

static PyObject *
PCAPObject_set_buffer_size(PCAPObject *self, PyObject *args)
{
    int ecode;
    int buffer_size;

    if (!PyArg_ParseTuple(args, "i:set_buffer_size", &buffer_size))
	return NULL;
    ecode = pcap_set_buffer_size(self->pcap, buffer_size);
    if (ecode)
	return PyErr_Format(
	    PCAPError,
	    "set_buffer_size(): capture handle has already been activated");
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_set_buffer_size_doc,
"set_buffer_size(buffer_size) -> None\n\
\n\
set_buffer_size() set the buffer size for a not-yet-activated capture\n\
handle. It is a wrapper for pcap_set_buffer_size() Packet Capture\n\
library routine.");

static PyObject *
PCAPObject_set_promisc(PCAPObject *self, PyObject *args)
{
    int ecode, promisc;
    PyObject *opromisc;

    if (!PyArg_ParseTuple(args, "O!:set_promisc", &PyBool_Type, &opromisc))
	return NULL;
    promisc = opromisc == Py_False ? 0 : 1;
    ecode = pcap_set_promisc(self->pcap, promisc);
    if (ecode)
	return PyErr_Format(
	    PCAPError,
	    "set_promisc(): capture handle has already been activated");
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_set_promisc_doc,
"set_promisc(boolean) -> None\n\
\n\
set_promisc() set promiscuous mode for a not-yet-activated capture\n\
handle. It is a wrapper for pcap_set_promisc() Packet Capture\n\
library routine.");

static PyObject *
PCAPObject_set_rfmon(PCAPObject *self, PyObject *args)
{
    int ecode, rfmon;
    PyObject *orfmon;

    if (!PyArg_ParseTuple(args, "O!:set_rfmon", &PyBool_Type, &orfmon))
	return NULL;
    rfmon = orfmon == Py_False ? 0 : 1;
    ecode = pcap_set_rfmon(self->pcap, rfmon);
    if (ecode)
	return PyErr_Format(
	    PCAPError,
	    "set_rfmon(): capture handle has already been activated");
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_set_rfmon_doc,
"set_rfmon(boolean) -> None\n\
\n\
set_rfmon() set monitor mode for a not-yet-activated capture\n\
handle. It is a wrapper for pcap_set_rfmon() Packet Capture\n\
library routine.");

static PyObject *
PCAPObject_set_snaplen(PCAPObject *self, PyObject *args)
{
    int ecode, snaplen;

    if (!PyArg_ParseTuple(args, "i:set_snaplen", &snaplen))
	return NULL;
    ecode = pcap_set_snaplen(self->pcap, snaplen);
    if (ecode)
	return PyErr_Format(
	    PCAPError,
	    "set_snaplen(): capture handle has already been activated");
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_set_snaplen_doc,
"set_snaplen(snaplen) -> None\n\
\n\
set_snaplen() set the snapshot length for a not-yet-activated capture\n\
handle. It is a wrapper for pcap_set_snaplen() Packet Capture\n\
library routine.");
    
static PyObject *
PCAPObject_set_timeout(PCAPObject *self, PyObject *args)
{
    int ecode, to_ms;

    if (!PyArg_ParseTuple(args, "i:set_timeout", &to_ms))
	return NULL;
    ecode = pcap_set_timeout(self->pcap, to_ms);
    if (ecode)
	return PyErr_Format(
	    PCAPError,
	    "set_timeout(): capture handle has already been activated");
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAPObject_set_timeout_doc,
"set_timeout(to_ms) -> None\n\
\n\
set_timeout() set the read timeout for a not-yet-activated capture\n\
handle. It is a wrapper for pcap_set_timeout() Packet Capture\n\
library routine.");

#if defined(OS_LINUX) || defined(OS_FREEBSD)
static PyObject *
PCAPObject_get_selectable_fd(PCAPObject *self)
{
    int fd;

    fd = pcap_get_selectable_fd(self->pcap);
    if (fd < 0)
	return PyErr_Format(PCAPError, "get_selectable_fd() failed");
    return Py_BuildValue("i", fd);
}

PyDoc_STRVAR(PCAPObject_get_selectable_fd_doc,
"get_selectable_fd() -> int\n\
\n\
get_selectable_fd() get a file descriptor on which a select() can\n\
be done for a live capture. It is a wrapper for pcap_get_selectable_fd()\n\
Packet Capture library routine.");
#endif /* defined(OS_LINUX) || defined(OS_FREEBSD) */

static PyObject *
PCAPObject_can_set_rfmon(PCAPObject *self)
{
    int ret;

    ret = pcap_can_set_rfmon(self->pcap);
    if (ret)
	Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

PyDoc_STRVAR(PCAPObject_can_set_rfmon_doc,
"can_set_rfmon() -> boolean\n\
\n\
can_set_rfmon() check whether monitor mode can be set for a not-\n\
yet-activated capture handle. It is a wrapper for pcap_can_set_rfmon()\n\
Packet Capture library routine.");

static PyMethodDef PCAPObjectMethods[] = {
    {"file", (PyCFunction) PCAPObject_file,
     METH_NOARGS, PCAPObject_file_doc},
    {"fileno", (PyCFunction) PCAPObject_fileno,
     METH_NOARGS, PCAPObject_fileno_doc},
    {"dump_open", (PyCFunction) PCAPObject_dump_open,
     METH_VARARGS, PCAPObject_dump_open_doc},
    {"dump_fopen", (PyCFunction) PCAPObject_dump_fopen,
     METH_VARARGS, PCAPObject_dump_fopen_doc},
    {"getnonblock", (PyCFunction) PCAPObject_getnonblock,
     METH_NOARGS, PCAPObject_getnonblock_doc},
    {"setnonblock", (PyCFunction) PCAPObject_setnonblock,
     METH_VARARGS, PCAPObject_setnonblock_doc},
    {"dispatch", (PyCFunction) PCAPObject_dispatch,
     METH_VARARGS, PCAPObject_dispatch_doc},
    {"loop", (PyCFunction) PCAPObject_loop,
     METH_VARARGS, PCAPObject_loop_doc},
    {"next", (PyCFunction) PCAPObject_next,
     METH_NOARGS, PCAPObject_next_doc},
    {"next_ex", (PyCFunction) PCAPObject_next_ex,
     METH_NOARGS, PCAPObject_next_ex_doc},
    {"inject", (PyCFunction) PCAPObject_inject,
     METH_VARARGS, PCAPObject_inject_doc},
    {"sendpacket", (PyCFunction) PCAPObject_sendpacket,
     METH_VARARGS, PCAPObject_sendpacket_doc},
    {"compile", (PyCFunction) PCAPObject_compile,
     METH_VARARGS, PCAPObject_compile_doc},
    {"setfilter", (PyCFunction) PCAPObject_setfilter,
     METH_VARARGS, PCAPObject_setfilter_doc},
    {"setdirection", (PyCFunction) PCAPObject_setdirection,
     METH_VARARGS, PCAPObject_setdirection_doc},
    {"breakloop", (PyCFunction) PCAPObject_breakloop,
     METH_NOARGS, PCAPObject_breakloop_doc},
    {"datalink", (PyCFunction) PCAPObject_datalink,
     METH_NOARGS, PCAPObject_datalink_doc},
    {"list_datalinks", (PyCFunction) PCAPObject_list_datalinks,
     METH_NOARGS, PCAPObject_list_datalinks_doc},
    {"snapshot", (PyCFunction) PCAPObject_snapshot,
     METH_NOARGS, PCAPObject_snapshot_doc},
    {"is_swapped", (PyCFunction) PCAPObject_is_swapped,
     METH_NOARGS, PCAPObject_is_swapped_doc},
    {"major_version", (PyCFunction) PCAPObject_major_version,
     METH_NOARGS, PCAPObject_major_version_doc},
    {"minor_version", (PyCFunction) PCAPObject_minor_version,
     METH_NOARGS, PCAPObject_minor_version_doc},
    {"stats", (PyCFunction) PCAPObject_stats,
     METH_NOARGS, PCAPObject_stats_doc},
    {"activate", (PyCFunction) PCAPObject_activate,
     METH_NOARGS, PCAPObject_activate_doc},
    {"set_buffer_size", (PyCFunction) PCAPObject_set_buffer_size,
     METH_VARARGS, PCAPObject_set_buffer_size_doc},
    {"set_promisc", (PyCFunction) PCAPObject_set_promisc,
     METH_VARARGS, PCAPObject_set_promisc_doc},
    {"set_rfmon", (PyCFunction) PCAPObject_set_rfmon,
     METH_VARARGS, PCAPObject_set_rfmon_doc},
    {"set_snaplen", (PyCFunction) PCAPObject_set_snaplen,
     METH_VARARGS, PCAPObject_set_snaplen_doc},
    {"set_timeout", (PyCFunction) PCAPObject_set_timeout,
     METH_VARARGS, PCAPObject_set_timeout_doc},
#if defined(OS_LINUX) || defined(OS_FREEBSD)
    {"get_selectable_fd", (PyCFunction) PCAPObject_get_selectable_fd,
     METH_NOARGS, PCAPObject_get_selectable_fd_doc},
#endif /* defined(OS_LINUX) || defined(OS_FREEBSD) */
    {"can_set_rfmon", (PyCFunction) PCAPObject_can_set_rfmon,
     METH_NOARGS, PCAPObject_can_set_rfmon_doc},
    {NULL, NULL, 0, NULL}
};

/* SPECIAL METHODS */

static void
PCAPObject_dealloc(PCAPObject *self)
{
    if (self->pcap)
	pcap_close(self->pcap);
    PyMem_Free((void *) self->fn);
    if (self->fo)
	PyFile_DecUseCount(self->fo);
    self->ob_type->tp_free((PyObject *) self);
}

static int
PCAPObject_init(PCAPObject *self, PyObject *args, PyObject *kwds)
{
    char *device = NULL;
    int snaplen = PCAP_SNAPLEN_DFLT, promisc = 0, to_ms = 0;

    if (!PyArg_ParseTuple(
	    args, "|siii:pcap.__init__", &device, &snaplen, &promisc, &to_ms
	    )
	)
	return -1;
    PCAPErrBuf[0] = 0;
    self->pcap = pcap_open_live(device, snaplen, promisc, to_ms, PCAPErrBuf);
    if (!self->pcap) {
	(void) PyErr_Format(PCAPError, "pcap.__init__(): %s", PCAPErrBuf);
	return -1;
    }
    if (PCAPErrBuf[0]) {
	char *err = "pcap.__init__(): ",
	    buf[strlen(err) + strlen(PCAPErrBuf) + 1];

	(void) sprintf(buf, "%s%s", err,  PCAPErrBuf);
	(void) PyErr_WarnEx(PyExc_UserWarning, buf, 1);
    }
    return 0;
}

static PyObject *
PCAPObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PCAPObject *self;

    self = (PCAPObject *) type->tp_alloc(type, 0);
    if (self) {
	self->pcap = NULL;
	self->fn = NULL;
	self->fo = NULL;
    }
    return (PyObject *) self;
}

/* TYPE */

static PyTypeObject PCAPTypeObject = {
    PyObject_HEAD_INIT(NULL)
    0,						/* ob_size */
    "pcap.pcap",				/* tp_name */
    sizeof(PCAPObject),				/* tp_basicsize */
    0,						/* tp_itemsize */
    (destructor) PCAPObject_dealloc,		/* tp_dealloc */
    0,						/* tp_print */
    0,						/* tp_getattr */
    0,						/* tp_setattr */
    0,						/* tp_compare */
    0,						/* tp_repr */
    0,						/* tp_as_number */
    0,						/* tp_as_sequence */
    0,						/* tp_as_mapping */
    0,						/* tp_hash  */
    0,						/* tp_call */
    0,						/* tp_str */
    0,						/* tp_getattro */
    0,						/* tp_setattro */
    0,						/* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
    PCAPObjectDoc,				/* tp_doc */
    0,						/* tp_traverse */
    0,						/* tp_clear */
    0,						/* tp_richcompare */
    0,						/* tp_weaklistoffset */
    0,						/* tp_iter */
    0,						/* tp_iternext */
    PCAPObjectMethods,				/* tp_methods */
    0,						/* tp_members */
    0,						/* tp_getset */
    0,						/* tp_base */
    0,						/* tp_dict */
    0,						/* tp_descr_get */
    0,						/* tp_descr_set */
    0,						/* tp_dictoffset */
    (initproc) PCAPObject_init,			/* tp_init */
    0,						/* tp_alloc */
    (newfunc) PCAPObject_new,			/* tp_new */
};

/*****************************************************************************
 * MODULE METHODS
 *****************************************************************************/

static PyObject *
PCAP_pcap_lookupdev(PyObject *self)
{
    char *device;

    device = pcap_lookupdev(PCAPErrBuf);
    if (!device)
	return PyErr_Format(PCAPError, "pcap_lookupdev(): %s", PCAPErrBuf);
    return Py_BuildValue("s", device);
}

PyDoc_STRVAR(PCAP_pcap_lookupdev_doc,
"pcap_lookupdev() -> <str>\n\
\n\
pcap_lookupdev() find the default device on which to capture. It is a\n\
wrapper for corresponding pcap_lookupdev() Packet Capture library routine.");

static PyObject *
PCAP_pcap_lookupnet(PyObject *self, PyObject *args)
{
    int ecode;
    const char *device;
    char net[INET_ADDRSTRLEN], mask[INET_ADDRSTRLEN];
    bpf_u_int32 netp, maskp;

    if (!PyArg_ParseTuple(args, "s:pcap_lookupnet", &device))
	return NULL;
    ecode = pcap_lookupnet(device, &netp, &maskp, PCAPErrBuf);
    if (ecode < 0)
	return PyErr_Format(PCAPError, "pcap_lookupnet(): %s", PCAPErrBuf);
    if (!inet_ntop(AF_INET, (const void *) &netp, net, sizeof(net)))
	return PyErr_Format(
	    PCAPError, "pcap_lookupnet(): inet_ntop(): (%d %s)", errno,
	    strerror(errno)
	    );
    if (!inet_ntop(AF_INET, (const void *) &maskp, mask, sizeof(mask)))
	return PyErr_Format(
	    PCAPError, "pcap_lookupnet(): inet_ntop(): (%d, %s)", errno,
	    strerror(errno)
	    );
    return Py_BuildValue("{ssss}", "net", net, "mask", mask);
}

PyDoc_STRVAR(PCAP_pcap_lookupnet_doc,
"pcap_lookupnet(device) -> {'net': <str>, 'mask': <str>}\n\
\n\
pcap_lookupnet() find the IPv4 network number and netmask for a device.\n\
It is a wrapper for corresponding pcap_lookupnet() Packet Capture library\n\
routine.");

static PyObject *
PCAP_pcap_findalldevs(PyObject *self)
{
    int ecode, nd;
    pcap_if_t *ad, *pad;
    PyObject *ret;

    ecode = pcap_findalldevs(&ad, PCAPErrBuf);
    if (ecode < 0)
	return PyErr_Format(PCAPError, "pcap_findalldevs(): %s", PCAPErrBuf);
    for (pad = ad, nd = 0; pad; pad = pad->next)
	nd++;
    ret = PyTuple_New((Py_ssize_t) nd);
    if (!ret) {
	pcap_freealldevs(ad);
	return NULL;
    }
    for (pad = ad, nd = 0; pad; pad = pad->next, nd++) {
	PyObject *val = __PCAPIfToDict((const pcap_if_t *) pad);

	if (!val) {
	    pcap_freealldevs(ad);
	    Py_DECREF(ret);
	    return NULL;
	}
	PyTuple_SET_ITEM(ret, (Py_ssize_t) nd, val);
    }
    pcap_freealldevs(ad);
    return ret;
}

PyDoc_STRVAR(PCAP_pcap_findalldevs_doc,
"pcap_findalldevs() -> (device, device,...)\n\
\n\
pcap_findalldevs() get a list of capture devices. It is a wrapper for\n\
corresponding pcap_findalldevs() Packet Capture library routine.\n\
\n\
A device is a dictionary of the following format:\n\
  {'name': <str>, # 'eth0' for example\n\
   'description': <str> or None,\n\
   'addresses': (address, address,...) # see below\n\
   'flags': <int> # interface flags\n\
  }\n\
and where an address is in turn a dictionary of the following format:\n\
  {'addr': (<str>, <int>), # (address, address family)\n\
   'netmask': (<str>, <int>) or None, # (address, address family)\n\
   'broadaddr': (<str>, <int>) or None, # (address, address family)\n\
   'dstaddr': (<str>, <int>) or None, # (address, address family)\n\
  }\n\
Note: address family may have the values pcap.AF_INET, pcap.AF_INET6\n\
or pcap.AF_LINK (on Linux, pcap.AF_LINK is the constant AF_PACKET\n\
and on FreeBSD, pcap.AF_LINK is the constant AF_LINK.");

static PyObject *
PCAP_pcap_create(PyObject *self, PyObject *args)
{
    const char *source = NULL;
    PCAPObject *ret;

    if (!PyArg_ParseTuple(args, "|s:pcap_create", &source))
	return NULL;
    ret = PyObject_New(PCAPObject, &PCAPTypeObject);
    if (!ret)
	return NULL;
    ret->pcap = pcap_create(source, PCAPErrBuf);
    if (!ret->pcap) {
	PyObject_Del((PyObject *) ret);
	return PyErr_Format(PCAPError, "pcap_create(): %s", PCAPErrBuf);
    }
    ret->fn = NULL;
    ret->fo = NULL;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAP_pcap_create_doc,
"pcap_create([source]) -> pcap object\n\
\n\
pcap_create() create a live capture handle. It is a wrapper for\n\
corresponding pcap_create() Packet Capture library routine.\n\
\n\
When pcap_create() is executed without argument, packets are\n\
are captured from all interfaces. See PCAP library documentation\n\
for more details.");

static PyObject *
PCAP_pcap_open_live(PyObject *self, PyObject *args)
{
    return PyObject_Call((PyObject *) &PCAPTypeObject, args, NULL);
}

PyDoc_STRVAR(PCAP_pcap_open_live_doc,
"pcap_open_live(device [, snaplen, promisc, to_ms]) -> pcap object\n\
\n\
pcap_open_live() open a device for capturing. It is a wrapper for\n\
corresponding pcap_open_live() Packet Capture library routine.\n\
\n\
Default values for `snaplen', `promisc' and `to_ms' are respectively\n\
`pcap.PCAP_SNAPLEN_DFLT' (65535), 0 and 0.\n\
\n\
Note: `pcap.pcap_open_live()' and `pcap.pcap()' (pcap object contructor)\n\
are equivalent.");

static PyObject *
PCAP_pcap_open_dead(PyObject *self, PyObject *args)
{
    int linktype = DLT_EN10MB, snaplen = PCAP_SNAPLEN_DFLT;
    PCAPObject *ret;

    if (!PyArg_ParseTuple(args, "|ii:pcap_open_dead", &linktype, &snaplen))
	return NULL;
        ret = PyObject_New(PCAPObject, &PCAPTypeObject);
    if (!ret)
	return NULL;
    ret->pcap = pcap_open_dead(linktype, snaplen);
    if (!ret->pcap) {
	PyObject_Del((PyObject *) ret);
	return PyErr_Format(PCAPError, "pcap_open_dead() failed");
    }
    ret->fn = NULL;
    ret->fo = NULL;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAP_pcap_open_dead_doc,
"pcap_open_dead([linktype, snaplen]) -> pcap object\n\
\n\
pcap_open_dead() open a fake pcap_t for compiling filters or opening a\n\
capture for output. It is a wrapper for corresponding pcap_open_live()\n\
Packet Capture library routine.\n\
\n\
Default values for `linktype' and `snaplen' are respectively\n\
`pcap.DLT_EN10MB' and `pcap.PCAP_SNAPLEN_DFLT' (65535)");

static PyObject *
PCAP_pcap_open_offline(PyObject *self, PyObject *args)
{
    const char *fname;
    char *fn;
    PCAPObject *ret;

    if (!PyArg_ParseTuple(args, "s:pcap_open_offline", &fname))
	return NULL;
    fn = (char *) PyMem_Malloc(strlen(fname) + 1);
    if (!fn)
	return PyErr_NoMemory();
    (void) strcpy(fn, fname);
    ret = PyObject_New(PCAPObject, &PCAPTypeObject);
    if (!ret) {
	PyMem_Free((void *) fn);
	return NULL;
    }
    ret->pcap = pcap_open_offline(fname, PCAPErrBuf);
    if (!ret->pcap) {
	PyMem_Free((void *) fn);
	PyObject_Del((PyObject *) ret);
	return PyErr_Format(PCAPError, "pcap_open_offline(): %s", PCAPErrBuf);
    }
    ret->fn = fn;
    ret->fo = NULL;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAP_pcap_open_offline_doc,
"pcap_open_offline(fname) -> pcap object\n\
\n\
pcap_open_offline() open a saved capture file for reading. It is a wrapper\n\
for corresponding pcap_open_offline() Packet Capture library routine.");

static PyObject *
PCAP_pcap_fopen_offline(PyObject *self, PyObject *args)
{
    char *fn, *fname;
    FILE *fp;
    pcap_t *pcap;
    PyFileObject *fo;
    PCAPObject *ret;

    if (!PyArg_ParseTuple(args, "O!:fopen_offline", &PyFile_Type, &fo))
	return NULL;
    fp = PyFile_AsFile((PyObject *) fo);
    PyFile_IncUseCount(fo);
    pcap = pcap_fopen_offline(fp, PCAPErrBuf);
    if (!pcap) {
	PyFile_DecUseCount(fo);
	return PyErr_Format(PCAPError, "fopen_offline(): %s", PCAPErrBuf);
    }
    fname = PyString_AS_STRING(PyFile_Name((PyObject *) fo));
    fn = (char *) PyMem_Malloc(strlen(fname) + 1);
    if (!fn) {
	pcap_close(pcap);
	Py_INCREF(fo);
	PyFile_DecUseCount(fo);
	return PyErr_NoMemory();
    }
    (void) strcpy(fn, fname);
    ret = PyObject_New(PCAPObject, &PCAPTypeObject);
    if (!ret) {
	pcap_close(pcap);
	Py_INCREF(fo);
	PyFile_DecUseCount(fo);
	PyMem_Free((void *) fn);
	return NULL;
    }
    ret->pcap = pcap;
    ret->fn = fn;
    Py_INCREF(fo);
    ret->fo = fo;
    return (PyObject *) ret;
}

PyDoc_STRVAR(PCAP_pcap_fopen_offline_doc,
"pcap_fopen_offline(fp) -> pcap object\n\
\n\
pcap_fopen_offline() open a saved capture file for reading. It is a wrapper\n\
for corresponding pcap_fopen_offline() Packet Capture library routine.\n\
\n\
Argument `fp' is a file object. File object `fp' should have been opened\n\
with mode `wb'.");

static PyObject *
PCAP_pcap_dump(PyObject *self, PyObject *args)
{
    struct pcap_pkthdr hdr;
    PCAPDumperObject *pd;
    PyObject *ohdr;
    u_char *sp;
    int splen;

    if (!PyArg_ParseTuple(
	    args, "O!O!s#:pcap_dump", &PCAPDumperTypeObject, &pd,
	    &PyDict_Type, &ohdr, &sp, &splen))
	return NULL;
    if (__PCAPDictToPktHdr(ohdr, &hdr) < 0) {
    	if (PyErr_ExceptionMatches(PyExc_TypeError))
    	    PyErr_SetString(
    		PyExc_TypeError, "pcap_dump(): arg2 must be a dict of type:"
    		" {'ts': {'tv_sec': <int>, 'tv_usec': <int>}, 'caplen': <int>,"
    		" 'len': <int>}"
    		);
    	return NULL;
    }
    pcap_dump((u_char *) pd->pd, &hdr, sp);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(PCAP_pcap_dump_doc,
"pcap_dump(user, h, sp) -> None\n\
\n\
pcap_dump() write a packet to a capture file. It is a wrapper for\n\
corresponding pcap_dump() Packet Capture library routine.\n\
\n\
Argument `user' must be a pcap dumper object (as returned by `dump_open()'\n\
method of a pcap object instance).\n\
Argument `h' must be a Python dictionary which is a wrapper for\n\
`struct pcap_pkthdr' defined in PCAP library. See `loop()' documentation\n\
for a description of this dictionary.\n\
Last argument `sp' is a (raw) string.");

static PyObject *
PCAP_pcap_lib_version(PyObject *self)
{
    return Py_BuildValue("s", pcap_lib_version());
}

PyDoc_STRVAR(PCAP_pcap_lib_version_doc,
"pcap_lib_version() -> <str>\n\
\n\
pcap_lib_version() get the version information for libpcap. It is a wrapper\n\
for corresponding pcap_lib_version() Packet Capture library routine.");

static PyObject *
PCAP_pcap_datalink_name_to_val(PyObject *self, PyObject *args)
{
    int dlt;
    const char *name;

    if (!PyArg_ParseTuple(args, "s:pcap_datalink_name_to_val", &name))
	return NULL;
    dlt = pcap_datalink_name_to_val(name);
    if (dlt < 0)
	return PyErr_Format(
	    PCAPError,
	    "pcap_datalink_name_to_val(): %s: invalid data link name", name
	    );
    return Py_BuildValue("i", dlt);
}

PyDoc_STRVAR(PCAP_pcap_datalink_name_to_val_doc,
"pcap_datalink_name_to_val(name) -> <int>\n\
\n\
pcap_datalink_name_to_val() get the link-layer header type value\n\
corresponding to a header type name. It is a wrapper for corresponding\n\
pcap_datalink_name_to_val() Packet Capture library routine.");

static PyObject *
PCAP_pcap_datalink_val_to_name(PyObject *self, PyObject *args)
{
    int dlt;
    const char *name;

    if (!PyArg_ParseTuple(args, "i:pcap_datalink_val_to_name", &dlt))
	return NULL;
    name = pcap_datalink_val_to_name(dlt);
    if (!name)
	return PyErr_Format(
	    PCAPError,
	    "pcap_datalink_val_to_name(): %d: invalid data link type", dlt
	    );
    return PyString_FromString(name);
}

PyDoc_STRVAR(PCAP_pcap_datalink_val_to_name_doc,
"pcap_datalink_val_to_name(dlt) -> <str>\n\
\n\
pcap_datalink_val_to_name() get a name for a link-layer header type value.\n\
It is a wrapper for corresponding pcap_datalink_val_to_name() Packet\n\
Capture library routine.");

static PyObject *
PCAP_pcap_datalink_val_to_description(PyObject *self, PyObject *args)
{
    int dlt;
    const char *description;

    if (!PyArg_ParseTuple(args, "i:pcap_datalink_val_to_description", &dlt))
	return NULL;
    description = pcap_datalink_val_to_description(dlt);
    if (!description)
	return PyErr_Format(
	    PCAPError,
	    "pcap_datalink_val_to_description(): %d: invalid data link type",
	    dlt
	    );
    return PyString_FromString(description);
}

PyDoc_STRVAR(PCAP_pcap_datalink_val_to_description_doc,
"pcap_datalink_val_to_description(dlt) -> <str>\n\
\n\
pcap_datalink_val_to_description() get a short description for a\n\
link-layer header type value. It is a wrapper for corresponding\n\
pcap_datalink_val_to_description() Packet Capture library routine.");

static PyMethodDef PCAPMethods[] = {
    {"pcap_lookupdev", (PyCFunction) PCAP_pcap_lookupdev,
     METH_VARARGS, PCAP_pcap_lookupdev_doc},
    {"pcap_lookupnet", (PyCFunction) PCAP_pcap_lookupnet,
     METH_VARARGS, PCAP_pcap_lookupnet_doc},
    {"pcap_findalldevs", (PyCFunction) PCAP_pcap_findalldevs,
     METH_VARARGS, PCAP_pcap_findalldevs_doc},
    {"pcap_create", (PyCFunction) PCAP_pcap_create,
     METH_VARARGS, PCAP_pcap_create_doc},
    {"pcap_open_live", (PyCFunction) PCAP_pcap_open_live,
     METH_VARARGS, PCAP_pcap_open_live_doc},
    {"pcap_open_dead", (PyCFunction) PCAP_pcap_open_dead,
     METH_VARARGS, PCAP_pcap_open_dead_doc},
    {"pcap_open_offline", (PyCFunction) PCAP_pcap_open_offline,
     METH_VARARGS, PCAP_pcap_open_offline_doc},
    {"pcap_fopen_offline", (PyCFunction) PCAP_pcap_fopen_offline,
     METH_VARARGS, PCAP_pcap_fopen_offline_doc},
    {"pcap_dump", (PyCFunction) PCAP_pcap_dump,
     METH_VARARGS, PCAP_pcap_dump_doc},
    {"pcap_lib_version", (PyCFunction) PCAP_pcap_lib_version,
     METH_VARARGS, PCAP_pcap_lib_version_doc},
    {"pcap_datalink_name_to_val", (PyCFunction) PCAP_pcap_datalink_name_to_val,
     METH_VARARGS, PCAP_pcap_datalink_name_to_val_doc},
    {"pcap_datalink_val_to_name", (PyCFunction) PCAP_pcap_datalink_val_to_name,
     METH_VARARGS, PCAP_pcap_datalink_val_to_name_doc},
    {"pcap_datalink_val_to_description",
     (PyCFunction) PCAP_pcap_datalink_val_to_description,
     METH_VARARGS, PCAP_pcap_datalink_val_to_description_doc},
    {NULL, NULL, 0, NULL}
};

/*****************************************************************************
 * MODULE INITIALIZATION
 *****************************************************************************/

PyDoc_STRVAR(PCAPDoc,
"pcap module - A wrapper for Packet Capture library\n\
\n\
This module intends to be an exhaustive wrapper for the well known\n\
Packet Capture library. It defines 3 new objects:\n\
- pcap object which is a wrapper for `pcap_t' of PCAP library\n\
- pcap_dumper object which is a wrapper for `pcap_dumper_t' of PCAP library\n\
- bpf_program object which is a wrapper for `struct bpf_program' used in\n\
  PCAP library\n\
\n\
In this module, each PCAP library function whose generic prototype is\n\
`type pcap_func (pcap_t *, ...)' is implemented as a method (named `func')\n\
of pcap object whose returned value is (Python) `type' (None if `type'\n\
is `void'). For example, the function `int pcap_inject (pcap_t * p,\n\
const void * buf, size_t size)' becomes the method `pcap.inject(<str>)',\n\
the latter returning a (Python) integer.\n\
\n\
Similary, each PCAP library function whose generic prototype is\n\
`type pcap_func (pcap_dumper_t *, ...)' is implemented as a method\n\
(named `func') of pcap_dumper object.\n\
Note that a pcap_dumper object cannot be created directly. It can only be\n\
created using the `dump_open()' method of a pcap object instance.\n\
\n\
As above, each PCAP library function whose generic prototype is\n\
`type pcap_func (struct bpf_program *, ...)' is implemented as a method\n\
(named `func') of bpf_program object.\n\
Note that a bpf_program object cannot be created directly. It can only be\n\
created using the `compile()' method of a pcap object instance.\n\
\n\
All remaining PCAP library functions are implemented as methods of pcap\n\
module.\n\
\n\
Module defines only one exception: `error'. This exception is accompagnied\n\
with a string value which is generally the error message generated by\n\
PCAP library (if not, it is a pcap module specific error).\n\
\n\
Module pcap defines some constants such as AF_INET, AF_INET6, AF_LINK,\n\
DLT_* and PCAP_* (see html documentation for more details).\n\
\n\
See PCAP library documentation (http://www.tcpdump.org) for more details.\n\
Also, you can have a look in subdirectory `examples' you will find in the\n\
distribution.");

PyMODINIT_FUNC
initpcap(void)
{
    PyObject *m;

    if (PyType_Ready(&PCAPBPFProgramTypeObject) < 0)
        return;
    if (PyType_Ready(&PCAPDumperTypeObject) < 0)
        return;
    if (PyType_Ready(&PCAPTypeObject) < 0)
        return;
    m = Py_InitModule3("pcap", PCAPMethods, PCAPDoc);
    if (!m)
	return;
    Py_INCREF(&PCAPBPFProgramTypeObject);
    if (PyModule_AddObject(
	    m, "bpf_program", (PyObject *) &PCAPBPFProgramTypeObject
	    ))
	return;
    Py_INCREF(&PCAPDumperTypeObject);
    if (PyModule_AddObject(
	    m, "pcap_dumper", (PyObject *) &PCAPDumperTypeObject
	    ))
	return;
    Py_INCREF(&PCAPTypeObject);
    if (PyModule_AddObject(m, "pcap", (PyObject *) &PCAPTypeObject))
	return;
    PCAPError = PyErr_NewException("pcap.error", NULL, NULL);
    if (!PCAPError)
	return;
    Py_INCREF(PCAPError);
    if (PyModule_AddObject(m, "error", PCAPError))
	return;
    __PCAPAddConstant(m);
}

/*****************************************************************************
 * LOCAL FUNCTION DEFINITIONS
 *****************************************************************************/

static void
__PCAPAddConstant(PyObject *m)
{
    PyModule_AddIntConstant(m, "AF_INET", AF_INET);
    PyModule_AddIntConstant(m, "AF_INET6", AF_INET6);
#if defined(OS_LINUX)
    PyModule_AddIntConstant(m, "AF_LINK", AF_PACKET);
#elif defined(OS_FREEBSD)
    PyModule_AddIntConstant(m, "AF_LINK", AF_LINK);
#endif
    PyModule_AddIntConstant(m, "PCAP_SNAPLEN_DFLT", PCAP_SNAPLEN_DFLT);
    PyModule_AddIntConstant(m, "PCAP_IF_LOOPBACK", PCAP_IF_LOOPBACK);
    PyModule_AddIntConstant(m, "PCAP_D_IN", PCAP_D_IN);
    PyModule_AddIntConstant(m, "PCAP_D_OUT", PCAP_D_OUT);
    PyModule_AddIntConstant(m, "PCAP_D_INOUT", PCAP_D_INOUT);
#ifdef DLT_NULL
    PyModule_AddIntConstant(m, "DLT_NULL", DLT_NULL);
#endif /* DLT_NULL */
#ifdef DLT_EN10MB
    PyModule_AddIntConstant(m, "DLT_EN10MB", DLT_EN10MB);
#endif /* DLT_EN10MB */
#ifdef DLT_IEEE802
    PyModule_AddIntConstant(m, "DLT_IEEE802", DLT_IEEE802);
#endif /* DLT_IEEE802 */
#ifdef DLT_ARCNET
    PyModule_AddIntConstant(m, "DLT_ARCNET", DLT_ARCNET);
#endif /* DLT_ARCNET */
#ifdef DLT_SLIP
    PyModule_AddIntConstant(m, "DLT_SLIP", DLT_SLIP);
#endif /* DLT_SLIP */
#ifdef DLT_PPP
    PyModule_AddIntConstant(m, "DLT_PPP", DLT_PPP);
#endif /* DLT_PPP */
#ifdef DLT_FDDI
    PyModule_AddIntConstant(m, "DLT_FDDI", DLT_FDDI);
#endif /* DLT_FDDI */
#ifdef DLT_ATM_RFC1483
    PyModule_AddIntConstant(m, "DLT_ATM_RFC1483", DLT_ATM_RFC1483);
#endif /* DLT_ATM_RFC1483 */
#ifdef DLT_RAW
    PyModule_AddIntConstant(m, "DLT_RAW", DLT_RAW);
#endif /* DLT_RAW */
#ifdef DLT_PPP_SERIAL
    PyModule_AddIntConstant(m, "DLT_PPP_SERIAL", DLT_PPP_SERIAL);
#endif /* DLT_PPP_SERIAL */
#ifdef DLT_PPP_ETHER
    PyModule_AddIntConstant(m, "DLT_PPP_ETHER", DLT_PPP_ETHER);
#endif /* DLT_PPP_ETHER */
#ifdef DLT_C_HDLC
    PyModule_AddIntConstant(m, "DLT_C_HDLC", DLT_C_HDLC);
#endif /* DLT_C_HDLC */
#ifdef DLT_IEEE802_11
    PyModule_AddIntConstant(m, "DLT_IEEE802_11", DLT_IEEE802_11);
#endif /* DLT_IEEE802_11 */
#ifdef DLT_FRELAY
    PyModule_AddIntConstant(m, "DLT_FRELAY", DLT_FRELAY);
#endif /* DLT_FRELAY */
#ifdef DLT_LOOP
    PyModule_AddIntConstant(m, "DLT_LOOP", DLT_LOOP);
#endif /* DLT_LOOP */
#ifdef DLT_LINUX_SLL
    PyModule_AddIntConstant(m, "DLT_LINUX_SLL", DLT_LINUX_SLL);
#endif /* DLT_LINUX_SLL */
#ifdef DLT_LTALK
    PyModule_AddIntConstant(m, "DLT_LTALK", DLT_LTALK);
#endif /* DLT_LTALK */
#ifdef DLT_PFLOG
    PyModule_AddIntConstant(m, "DLT_PFLOG", DLT_PFLOG);
#endif /* DLT_PFLOG */
#ifdef DLT_PRISM_HEADER
    PyModule_AddIntConstant(m, "DLT_PRISM_HEADER", DLT_PRISM_HEADER);
#endif /* DLT_PRISM_HEADER */
#ifdef DLT_IP_OVER_FC
    PyModule_AddIntConstant(m, "DLT_IP_OVER_FC", DLT_IP_OVER_FC);
#endif /* DLT_IP_OVER_FC */
#ifdef DLT_SUN_ATM
    PyModule_AddIntConstant(m, "DLT_SUN_ATM", DLT_SUN_ATM);
#endif /* DLT_SUN_ATM */
#ifdef DLT_IEEE802_11_RADIO
    PyModule_AddIntConstant(m, "DLT_IEEE802_11_RADIO", DLT_IEEE802_11_RADIO);
#endif /* DLT_IEEE802_11_RADIO */
#ifdef DLT_ARCNET_LINUX
    PyModule_AddIntConstant(m, "DLT_ARCNET_LINUX", DLT_ARCNET_LINUX);
#endif /* DLT_ARCNET_LINUX */
#ifdef DLT_LINUX_IRDA
    PyModule_AddIntConstant(m, "DLT_LINUX_IRDA", DLT_LINUX_IRDA);
#endif /* DLT_LINUX_IRDA */
#ifdef DLT_LINUX_LAPD
    PyModule_AddIntConstant(m, "DLT_LINUX_LAPD", DLT_LINUX_LAPD);
#endif /* DLT_LINUX_LAPD */
}

static PyObject *__PCAPPktHdrToDict(const struct pcap_pkthdr *hdr)
{
    return Py_BuildValue(
	"{s{slsl}sIsI}", "ts", "tv_sec",  hdr->ts.tv_sec, "tv_usec",
	hdr->ts.tv_usec, "caplen", hdr->caplen, "len", hdr->len
	);
}

static int
__PCAPDictToPktHdr(PyObject *ohdr, struct pcap_pkthdr *hdr)
{
    int ret = 0;
    static char *hdrlist[] = {"ts", "caplen", "len", NULL};
    static char *tslist[] = {"tv_sec", "tv_usec", NULL};
    PyObject *ots = NULL, *args = PyTuple_New(0);

    if (!args)
	return -1;
    if (!PyArg_ParseTupleAndKeywords(
	    args, ohdr, "O!II;", hdrlist, &PyDict_Type, &ots,
	    &hdr->caplen, &hdr->len
	    )) {
	ret = -1;
	goto fail;
    }
    if (!PyArg_ParseTupleAndKeywords(
	    args, ots, "II;", tslist, &hdr->ts.tv_sec, &hdr->ts.tv_usec)) {
	ret = -1;
	goto fail;
    }
  fail:
    Py_XDECREF(ots);
    Py_DECREF(args);
    return ret;
}

static PyObject *
__PCAPIfToDict(const pcap_if_t *ifp)
{
    int na;
    pcap_addr_t *pa;
    PyObject *addrs;

    for (pa = ifp->addresses, na = 0; pa; pa = pa->next)
	if (pa->addr->sa_family == AF_INET || pa->addr->sa_family == AF_INET6
#if defined(OS_LINUX)
	    || pa->addr->sa_family == AF_PACKET)
#elif defined(OS_FREEBSD)
	    || pa->addr->sa_family == AF_LINK)
#else
	    )
#endif
	    na++;
    if (!na)
	addrs = Py_None;
    else {
	addrs = PyTuple_New((Py_ssize_t) na);
	if (!addrs)
	    return NULL;
	for (pa = ifp->addresses, na = 0; pa; pa = pa->next) {
	    PyObject *val;
	    
	    if (pa->addr->sa_family != AF_INET &&
		pa->addr->sa_family != AF_INET6
#if defined(OS_LINUX)
		&& pa->addr->sa_family != AF_PACKET)
#elif defined(OS_FREEBSD)
		&& pa->addr->sa_family != AF_LINK)
#else
	    )
#endif
		continue;
	    val = __PCAPAddrToDict((const pcap_addr_t *) pa);
	    if (!val) {
		Py_DECREF(addrs);
		return NULL;
	    }
	    PyTuple_SET_ITEM(addrs, (Py_ssize_t) na, val);
	    na++;
	}
    }
    return Py_BuildValue(
	"{sssssNsI}", "name", ifp->name, "description", ifp->description,
	"addresses", addrs, "flags", ifp->flags
	);
}

static PyObject *
__PCAPAddrToDict(const pcap_addr_t *a)
{
    PyObject *addr = NULL, *netmask = NULL, *broadaddr = NULL, *dstaddr = NULL;

    addr = __PCAPSockAddrToChar(a->addr);
    if (!addr)
	goto fail;
    netmask = __PCAPSockAddrToChar(a->netmask);
    if (!netmask)
	goto fail;
    broadaddr = __PCAPSockAddrToChar(a->broadaddr);
    if (!broadaddr)
	goto fail;
    dstaddr = __PCAPSockAddrToChar(a->dstaddr);
    if (!dstaddr)
	goto fail;
    return Py_BuildValue(
	"{sNsNsNsN}", "addr", addr, "netmask", netmask, "broadaddr", broadaddr,
	"dstaddr", dstaddr
	);
  fail:
    Py_XDECREF(addr);
    Py_XDECREF(netmask);
    Py_XDECREF(broadaddr);
    Py_XDECREF(dstaddr);
    return NULL;
}

static PyObject *
__PCAPSockAddrToChar(const struct sockaddr *sa)
{
    socklen_t salen;

    if (!sa)
	Py_RETURN_NONE;
    switch (sa->sa_family) {
    case AF_INET:
	salen = sizeof(struct sockaddr_in);
	break;
    case AF_INET6:
	salen = sizeof(struct sockaddr_in6);
	break;
#if defined(OS_LINUX)
    case AF_PACKET:
#elif defined(OS_FREEBSD)
    case AF_LINK:
#endif
	break;
    default:
	Py_RETURN_NONE;
    }
    if (sa->sa_family == AF_INET || sa->sa_family == AF_INET6) {
	int ecode;
	char host[NI_MAXHOST];

	ecode = getnameinfo(
	    sa, salen, host, sizeof(host), NULL, 0, NI_NUMERICHOST
	    );
	if (ecode)
	    return PyErr_Format(
		PCAPError, "%s(): inet_ntop(): (%d %s)", __func__, ecode,
		gai_strerror(ecode)
		);
	return Py_BuildValue("(sB)", host, (u_char) sa->sa_family);
    }
    else {
#if defined(OS_LINUX)
	struct sockaddr_ll *sll = (struct sockaddr_ll *) sa;

	return Py_BuildValue(
	    "(OH)",
	    __PCAPAddrBinToTxt(
		(const unsigned char *) sll->sll_addr, (size_t) sll->sll_halen
		),
	    sll->sll_family
	    );
#elif defined(OS_FREEBSD)
	struct sockaddr_dl *sdl;

	return Py_BuildValue(
	    "(OB)",
	    __PCAPAddrBinToTxt(
		(const unsigned char *) LLADDR(sdl), (size_t) sdl->sdl_alen
		),
	    sdl->sdl_family
	    );
#endif	
    }
}

static PyObject *
__PCAPObject_ld(
    PyObject *self, PyObject *args, const char *fname,
    int (*pcap_fun)(pcap_t *, int, pcap_handler, u_char *)
    )
{
    int cnt, ecode;
    pcap_t *p = ((PCAPObject *) self)->pcap;
    char fmt[strlen(fname) + 7];
    PCAP_user_t u = {Py_None, p};
    PyObject *fun;

    sprintf(fmt, "iO|O:%s", fname);
    if (!PyArg_ParseTuple(args, fmt, &cnt, &fun, &u.user))
	return NULL;
    if (!PyCallable_Check(fun)) 
	return PyErr_Format(
	    PyExc_TypeError, "%s(): arg2 is not callable", fname
    	    );
    u.cb = fun;
    ecode = pcap_fun(p, cnt, __PCAPHandler, (u_char *) &u);
    if (ecode == -1)
	return PyErr_Format(PCAPError, "%s(): %s", fname, pcap_geterr(p));
    if (ecode == -2)
	if (PyErr_Occurred())
	    return NULL;
    if (!strcmp(fname, "loop"))
	Py_RETURN_NONE;
    return Py_BuildValue("i", ecode);
}

static void
__PCAPHandler(u_char *user, const struct pcap_pkthdr *h, const u_char *bytes)
{
    PCAP_user_t *u = (PCAP_user_t *) user;
    PyObject *ret, *oh = __PCAPPktHdrToDict(h);

    if (!oh) {
	pcap_breakloop(u->pcap);
	return;
    }
    ret = PyObject_CallFunction(
	u->cb, "ONs#", u->user, oh, (char *) bytes, h->caplen
	);
    if (!ret)
	pcap_breakloop(u->pcap);
    Py_XDECREF(ret);
}

static PyObject *
__PCAPAddrBinToTxt(const unsigned char *a, size_t alen)
{
    unsigned char buf[3 * alen], *p, *q;

    if (!a || !alen)
	Py_RETURN_NONE;
    for (p = (unsigned char *) a, q = buf; p - a < alen; p++, q += 3) {
	sprintf((char *) q, "%02hhx", *p);
	if (p - a < alen - 1)
	    sprintf((char *) q + 2, ":");
    }
    return PyString_FromString((char *) buf);
}
