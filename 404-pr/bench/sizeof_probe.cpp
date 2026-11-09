#include <parse.h>
template<std::size_t N> struct size_probe;
size_probe<sizeof(pdflib::page_item<pdflib::PAGE_CELL>)> probe_cell;
