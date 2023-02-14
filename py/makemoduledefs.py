"""
This pre-processor parses a single file containing a list of
MP_REGISTER_MODULE(module_name, obj_module)
These are used to generate a header with the required entries for
"mp_rom_map_elem_t mp_builtin_module_table[]" in py/objmodule.c
"""

from __future__ import print_function

import sys
import re
import io
import argparse


pattern = re.compile(r"\s*MP_REGISTER_MODULE\((.*?),\s*(.*?)\);", flags=re.DOTALL)


def find_module_registrations(filename):
    """Find any MP_REGISTER_MODULE definitions in the provided file.

    :param str filename: path to file to check
    :return: List[(module_name, obj_module)]
    """
    global pattern

    with io.open(filename, encoding="utf-8") as c_file_obj:
        return set(re.findall(pattern, c_file_obj.read()))


def generate_module_table_header(modules):
    """Generate header with module table entries for builtin modules.

    :param List[(module_name, obj_module)] modules: module defs
    :return: None
    """

    # Print header file for all external modules.
    mod_defs = set()
    print("// Automatically generated by makemoduledefs.py.\n")
    for module_name, obj_module in modules:
        mod_def = "MODULE_DEF_{}".format(module_name.upper())
        mod_defs.add(mod_def)
        if "," in obj_module:
            print(
                "ERROR: Call to MP_REGISTER_MODULE({}, {}) should be MP_REGISTER_MODULE({}, {})\n".format(
                    module_name, obj_module, module_name, obj_module.split(",")[0]
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            (
                "extern const struct _mp_obj_module_t {obj_module};\n"
                "#undef {mod_def}\n"
                "#define {mod_def} {{ MP_ROM_QSTR({module_name}), MP_ROM_PTR(&{obj_module}) }},\n"
            ).format(
                module_name=module_name,
                obj_module=obj_module,
                mod_def=mod_def,
            )
        )

    print("\n#define MICROPY_REGISTERED_MODULES \\")

    for mod_def in sorted(mod_defs):
        print("    {mod_def} \\".format(mod_def=mod_def))

    print("// MICROPY_REGISTERED_MODULES")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs=1, help="file with MP_REGISTER_MODULE definitions")
    args = parser.parse_args()

    modules = find_module_registrations(args.file[0])
    generate_module_table_header(sorted(modules))


if __name__ == "__main__":
    main()